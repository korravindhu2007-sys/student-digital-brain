"""Document processing service for NeuroNote."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from src.config import config
from src.database.repository import (
    create_document,
    get_document,
    get_document_by_hash,
    list_documents,
    save_chunks,
    update_document_status,
)
from src.llm.engine import LLMEngine as LLMService
from src.retrieval.retrieval_engine import RetrievalEngine
from src.utils.chunking import SemanticChunker
from src.utils.logging import setup_logging

logger = setup_logging(__name__)


@dataclass
class DocumentMetadata:
    """Document metadata."""
    filename: str
    file_path: Path
    file_size: int
    file_type: str
    page_count: int = 0
    pdf_hash: str = ""
    subject: str = "General"
    topic: str = "General"
    upload_date: datetime = field(default_factory=datetime.now)
    language: str = "en"
    status: str = "pending"


@dataclass
class ProcessingResult:
    """Document processing result."""
    success: bool
    document_id: Optional[int] = None
    status: str = "failed"
    error: Optional[str] = None
    chunk_count: int = 0
    page_count: int = 0
    extracted_chars: int = 0
    cache_hit: bool = False
    metadata: Optional[DocumentMetadata] = None


class DocumentService:
    """Service for document upload, processing, and retrieval."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self.db_path = db_path
        self.upload_dir = Path(config.upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        chunk_size = getattr(getattr(config, 'processing', None), 'chunk_size', None) or getattr(getattr(config, 'chunking', None), 'chunk_size_tokens', 800)
        chunk_overlap = getattr(getattr(config, 'processing', None), 'chunk_overlap', None) or getattr(getattr(config, 'chunking', None), 'chunk_overlap_tokens', 100)
        self.chunker = SemanticChunker(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        self.llm_service = LLMService()
        self.retrieval_engine = RetrievalEngine(db_path)

    def process_document(self, file: Any, metadata: Optional[dict[str, Any]] = None) -> ProcessingResult:
        """Process uploaded document through the complete pipeline.

        Pipeline: Upload → Validate → Extract → OCR if required → Clean → Chunk → Save → Return ID

        Args:
            file: Uploaded file object.
            metadata: Optional document metadata.

        Returns:
            ProcessingResult with document info.
        """
        start_time = datetime.now()
        logger.info("Starting document processing: %s", getattr(file, 'name', 'unknown'))

        try:
            # Step 1: Validate
            validation = self.validate_document(file)
            if not validation["valid"]:
                return ProcessingResult(success=False, status="rejected", error=validation["error"])

            # Step 2: Save uploaded file
            saved_path, original_name, file_hash = self._save_uploaded_file(file)

            # Step 3: Check for duplicates
            existing = get_document_by_hash(file_hash, db_path=self.db_path)
            if existing and existing.get("raw_text", "").strip():
                logger.info("Document already processed (cache hit): %s", file_hash)
                return ProcessingResult(
                    success=True,
                    document_id=existing.get("id"),
                    status="cached",
                    chunk_count=existing.get("chunk_count", 0),
                    page_count=existing.get("page_count", 0),
                    extracted_chars=len(existing.get("raw_text", "")),
                    cache_hit=True,
                )

            # Step 4: Extract text
            extraction_result = self.extract_document(saved_path)
            if not extraction_result["success"]:
                return ProcessingResult(success=False, status="failed", error=extraction_result["error"])

            raw_text = extraction_result["text"]
            pages = extraction_result["pages"]
            page_count = extraction_result["page_count"]

            # Step 5: Clean text
            cleaned_text = self.clean_document(raw_text)

            # Step 6: Chunk document
            chunks = self.chunk_document(cleaned_text, pages)

            # Step 7: Create metadata
            doc_metadata = DocumentMetadata(
                filename=original_name,
                file_path=saved_path,
                file_size=saved_path.stat().st_size,
                file_type=saved_path.suffix.lower().lstrip("."),
                page_count=page_count,
                pdf_hash=file_hash,
                subject=metadata.get("subject", "General") if metadata else "General",
                topic=metadata.get("topic", "General") if metadata else "General",
            )

            # Step 8: Save to database
            document_id = self._save_to_database(doc_metadata, cleaned_text, chunks, pages)

            execution_time = (datetime.now() - start_time).total_seconds()
            logger.info("Document processed successfully in %.2f seconds: ID=%d, chunks=%d",
                       execution_time, document_id, len(chunks))

            return ProcessingResult(
                success=True,
                document_id=document_id,
                status="completed",
                chunk_count=len(chunks),
                page_count=page_count,
                extracted_chars=len(cleaned_text),
                metadata=doc_metadata,
            )

        except Exception as exc:
            logger.exception("Document processing failed")
            return ProcessingResult(success=False, status="failed", error=str(exc))

    def validate_document(self, file: Any) -> dict[str, Any]:
        """Validate uploaded document.

        Args:
            file: Uploaded file object.

        Returns:
            Dict with validation result.
        """
        from src.ingestion.pdf_extractor import is_pdf_encrypted, validate_pdf
        try:
            # Check file exists
            if file is None:
                return {"valid": False, "error": "No file provided"}

            # Get file info
            if hasattr(file, 'name'):
                filename = file.name
                file_size = getattr(file, 'size', 0)
            elif isinstance(file, dict):
                filename = file.get("name", "unknown")
                file_size = file.get("size", 0)
            else:
                filename = str(file)
                file_size = 0

            # Check extension
            ext = Path(filename).suffix.lower()
            allowed_extensions = (
                getattr(config, 'supported_pdf_extensions', ['.pdf']) +
                getattr(config, 'supported_image_extensions', []) +
                getattr(config, 'supported_text_extensions', [])
            )
            if ext not in allowed_extensions:
                return {
                    "valid": False,
                    "error": f"Invalid file type '{ext}'. Allowed: {', '.join(allowed_extensions)}"
                }

            # Check size
            max_size = getattr(config, 'max_upload_bytes', 100 * 1024 * 1024)
            if file_size > max_size:
                return {
                    "valid": False,
                    "error": f"File too large ({file_size / 1024 / 1024:.1f}MB). Max: {max_size / 1024 / 1024:.0f}MB"
                }

            # For PDFs, check encryption
            if ext == ".pdf":
                temp_path = self._save_temp_file(file)
                try:
                    if is_pdf_encrypted(temp_path):
                        return {"valid": False, "error": "Encrypted PDFs are not supported"}
                    if not validate_pdf(temp_path):
                        return {"valid": False, "error": "Corrupted or invalid PDF file"}
                except Exception:
                    pass
                finally:
                    if temp_path.exists():
                        temp_path.unlink()

            return {"valid": True}

        except Exception as exc:
            logger.error("Validation failed: %s", exc)
            return {"valid": False, "error": f"Validation error: {exc}"}

    def extract_document(self, file_path: Path) -> dict[str, Any]:
        """Extract text from document.

        Args:
            file_path: Path to document.

        Returns:
            Dict with extracted text and metadata.
        """
        try:
            if file_path.suffix.lower() != ".pdf":
                return {
                    "success": False,
                    "error": f"Unsupported format: {file_path.suffix}. Only PDF supported in this phase.",
                }

            from src.ingestion.pdf_extractor import extract_text_from_pdf
            logger.info("Extracting text from: %s", file_path.name)
            result = extract_text_from_pdf(file_path)

            if not result or not result.get("text", "").strip():
                return {
                    "success": False,
                    "error": "Could not extract text. Try OCR-ready scans or text-based PDFs.",
                }

            return {
                "success": True,
                "text": result["text"],
                "pages": result.get("pages", []),
                "page_count": result.get("page_count", 0),
            }

        except Exception as exc:
            logger.exception("Text extraction failed")
            return {"success": False, "error": str(exc)}

    def clean_document(self, text: str) -> str:
        """Clean extracted text.

        Args:
            text: Raw extracted text.

        Returns:
            Cleaned text.
        """
        if not text:
            return ""

        # Remove excessive whitespace
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            stripped = ' '.join(line.split())
            cleaned_lines.append(stripped)

        # Remove empty lines
        cleaned_lines = [line for line in cleaned_lines if line]

        # Join with single newlines
        cleaned = '\n'.join(cleaned_lines)

        # Remove excessive newlines
        while '\n\n\n' in cleaned:
            cleaned = cleaned.replace('\n\n\n', '\n\n')

        return cleaned.strip()

    def chunk_document(self, text: str, pages: Optional[list[dict[str, Any]]] = None) -> list[dict[str, Any]]:
        """Chunk document into semantic segments.

        Args:
            text: Document text.
            pages: Optional page information.

        Returns:
            List of chunk dicts.
        """
        if not text:
            return []

        try:
            # Use semantic chunker
            chunks = self.chunker.chunk(text, pages=pages)

            # Enrich chunks with metadata
            for idx, chunk in enumerate(chunks):
                chunk["chunk_index"] = idx
                chunk["token_count"] = len(chunk.get("text", "").split())
                if pages:
                    page_num = chunk.get("page_number")
                    if page_num and page_num <= len(pages):
                        chunk["text"] = chunk.get("text", "")

            logger.info("Created %d semantic chunks", len(chunks))
            return chunks

        except Exception as exc:
            logger.exception("Chunking failed")
            # Fallback to simple chunking
            return self._fallback_chunk(text)

    def _fallback_chunk(self, text: str, chunk_size: int = 700, overlap: int = 150) -> list[dict[str, Any]]:
        """Fallback chunking if semantic chunker fails."""
        chunks = []
        words = text.split()
        for i in range(0, len(words), chunk_size - overlap):
            chunk_text = ' '.join(words[i:i + chunk_size])
            chunks.append({
                "text": chunk_text,
                "page_number": 1,
                "section_heading": "Section",
                "chunk_index": len(chunks),
                "token_count": len(chunk_text.split()),
            })
        return chunks

    def delete_document(self, document_id: int) -> bool:
        """Delete document and associated data.

        Args:
            document_id: Document ID.

        Returns:
            True if deleted successfully.
        """
        try:
            doc = get_document(document_id, db_path=self.db_path)
            if not doc:
                return False

            # Delete file if exists
            file_path = Path(doc.get("file_path", ""))
            if file_path.exists():
                file_path.unlink()

            logger.info("Delete requested for document %d", document_id)
            return True

        except Exception as exc:
            logger.error("Delete failed: %s", exc)
            return False

    def get_document(self, document_id: int) -> Optional[dict[str, Any]]:
        """Get document by ID.

        Args:
            document_id: Document ID.

        Returns:
            Document dict or None.
        """
        return get_document(document_id, db_path=self.db_path)

    def list_documents(self, subject: Optional[str] = None, status: Optional[str] = None,
                      limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        """List documents with optional filters.

        Args:
            subject: Filter by subject.
            status: Filter by status.
            limit: Maximum results.
            offset: Pagination offset.

        Returns:
            List of document dicts.
        """
        return list_documents(subject=subject, status=status, limit=limit, offset=offset, db_path=self.db_path)

    def _save_uploaded_file(self, file: Any) -> tuple[Path, str, str]:
        """Save uploaded file to upload directory.

        Returns:
            Tuple of (saved_path, original_filename, file_hash).
        """
        # Get filename
        if hasattr(file, 'name'):
            original_name = file.name
        elif isinstance(file, dict):
            original_name = file.get("name", "upload.pdf")
        else:
            original_name = str(file)

        # Create unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = f"{timestamp}_{Path(original_name).name}"
        dest_path = self.upload_dir / safe_name

        # Save file
        if hasattr(file, 'read'):
            with open(dest_path, 'wb') as f:
                shutil.copyfileobj(file, f)
        elif isinstance(file, bytes):
            dest_path.write_bytes(file)
        elif isinstance(file, dict) and 'content' in file:
            content = file['content']
            if isinstance(content, str):
                dest_path.write_text(content)
            else:
                dest_path.write_bytes(content)
        else:
            # Assume it's a path
            src = Path(file)
            if src.exists():
                shutil.copy(src, dest_path)
            else:
                raise FileNotFoundError(f"Source file not found: {file}")

        # Calculate hash
        file_hash = self._file_hash(dest_path)

        logger.info("File saved: %s (hash: %s)", dest_path.name, file_hash[:16])
        return dest_path, original_name, file_hash

    def _save_temp_file(self, file: Any) -> Path:
        """Save file temporarily for validation."""
        if hasattr(file, 'name'):
            original_name = file.name
        elif isinstance(file, dict):
            original_name = file.get("name", "temp.pdf")
        else:
            original_name = str(file)

        temp_path = self.upload_dir / f"temp_{Path(original_name).name}"
        if hasattr(file, 'read'):
            with open(temp_path, 'wb') as f:
                shutil.copyfileobj(file, f)
        elif isinstance(file, bytes):
            temp_path.write_bytes(file)
        return temp_path

    def _save_to_database(self, metadata: DocumentMetadata, raw_text: str,
                         chunks: list[dict[str, Any]], pages: list[dict[str, Any]]) -> int:
        """Save document and chunks to database.

        Returns:
            Document ID.
        """
        # Create document record
        doc_id = create_document(
            title=metadata.filename,
            file_type=metadata.file_type,
            file_path=str(metadata.file_path),
            file_size=metadata.file_size,
            subject=metadata.subject,
            topic=metadata.topic,
            pdf_hash=metadata.pdf_hash,
            page_count=metadata.page_count,
            raw_text=raw_text,
            structured_json=json.dumps({
                "source_name": metadata.filename,
                "source_path": str(metadata.file_path),
                "source_type": metadata.file_type,
                "pdf_hash": metadata.pdf_hash,
                "pages": pages,
                "subject": metadata.subject,
                "topic": metadata.topic,
            }),
        )

        # Save chunks
        save_chunks(doc_id, chunks)

        # Update status to completed
        update_document_status(doc_id, "completed")

        logger.info("Document saved to database: ID=%d", doc_id)
        return doc_id

    @staticmethod
    def _file_hash(path: Path) -> str:
        """Calculate SHA256 hash of file."""
        digest = hashlib.sha256()
        with path.open('rb') as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b''):
                digest.update(chunk)
        return digest.hexdigest()


# Global service instance
_document_service: Optional[DocumentService] = None


def get_document_service(db_path: Optional[Path] = None) -> DocumentService:
    """Get or create document service instance.

    Args:
        db_path: Optional database path.

    Returns:
        DocumentService instance.
    """
    global _document_service
    if _document_service is None or db_path:
        _document_service = DocumentService(db_path)
    return _document_service