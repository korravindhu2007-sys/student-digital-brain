"""Document processing orchestration service for NeuroNote."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from src.database.repository import (
    create_document,
    get_or_create_subject,
    update_document_status,
)
from src.ingestion.pdf_extractor import PDFExtractor
from src.llm.engine import LLMEngine
from src.ocr.processor import OCRProcessor
from src.parser.json_parser import JSONParser
from src.parser.text_processor import TextProcessor
from src.speech.transcriber import WhisperTranscriber
from src.utils.exceptions import ProcessingError
from src.utils.file_utils import validate_file
from src.utils.logging import setup_logging

logger = setup_logging(__name__)


class DocumentProcessor:
    """Orchestrate document processing from upload to structured storage.

    Coordinates PDF extraction, OCR, STT, LLM inference, and database
    persistence.
    """

    def __init__(self) -> None:
        self.text_processor = TextProcessor()
        self.json_parser = JSONParser()
        self.llm_engine = LLMEngine()
        self.ocr_processor = OCRProcessor()
        self.stt_transcriber: Optional[WhisperTranscriber] = None

    def process_file(
        self,
        file_path: Path,
        subject_name: str = "General",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Process an uploaded file end-to-end.

        Args:
            file_path: Path to the uploaded file.
            subject_name: Subject to associate with the document.
            metadata: Optional additional metadata.

        Returns:
            Dict with document_id, status, and processing details.

        Raises:
            ProcessingError: If processing fails.
        """
        # Validate file
        file_type, extension = validate_file(file_path)

        # Create database record
        subject_id = get_or_create_subject(subject_name)
        doc_id = create_document(
            title=file_path.stem,
            file_type=file_type,
            file_path=str(file_path),
            file_size=file_path.stat().st_size,
            subject_id=subject_id,
        )

        update_document_status(doc_id, "processing")

        try:
            result = self._process_by_type(
                doc_id=doc_id,
                file_path=file_path,
                file_type=file_type,
                subject_id=subject_id,
                metadata=metadata,
            )
            update_document_status(doc_id, "completed", raw_text=result.get("raw_text"))
            logger.info("Document %d processed successfully", doc_id)
            return {"document_id": doc_id, "status": "completed", **result}

        except Exception as e:
            error_msg = str(e)
            update_document_status(doc_id, "failed", error_message=error_msg)
            logger.error("Document %d processing failed: %s", doc_id, e)
            raise ProcessingError(
                f"Failed to process document: {e}",
                module="document_processor",
                document_id=doc_id,
            )

    def _process_by_type(
        self,
        doc_id: int,
        file_path: Path,
        file_type: str,
        subject_id: int,
        metadata: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Route to appropriate processor based on file type.

        Args:
            doc_id: Document ID.
            file_path: File path.
            file_type: File type.
            subject_id: Subject ID.
            metadata: Additional metadata.

        Returns:
            Processing result dict.
        """
        if file_type == "pdf":
            return self._process_pdf(doc_id, file_path, subject_id, metadata)
        elif file_type == "image":
            return self._process_image(doc_id, file_path, subject_id, metadata)
        elif file_type == "audio":
            return self._process_audio(doc_id, file_path, subject_id, metadata)
        elif file_type == "text":
            return self._process_text(doc_id, file_path, subject_id, metadata)
        else:
            raise ProcessingError(f"Unsupported file type: {file_type}", document_id=doc_id)

    def _process_pdf(
        self,
        doc_id: int,
        file_path: Path,
        subject_id: int,
        metadata: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Process a PDF document.

        Args:
            doc_id: Document ID.
            file_path: PDF file path.
            subject_id: Subject ID.
            metadata: Additional metadata.

        Returns:
            Processing result.
        """
        logger.info("Processing PDF: %s (doc_id=%d)", file_path.name, doc_id)

        # Extract text and metadata
        extractor = PDFExtractor(file_path)
        pdf_metadata = extractor.get_metadata()
        raw_text = extractor.extract_all_text()

        # Clean and chunk text
        cleaned_text = self.text_processor.clean_text(raw_text)
        chunks = self.text_processor.chunk_text(cleaned_text)

        # Process each chunk with LLM
        all_concepts: List[Dict[str, Any]] = []
        all_questions: List[Dict[str, Any]] = []

        for idx, chunk in enumerate(chunks):
            logger.info(
                "Processing chunk %d/%d for doc %d",
                idx + 1,
                len(chunks),
                doc_id,
            )
            try:
                extraction = self._extract_knowledge(chunk, subject_id)
                all_concepts.extend(extraction.get("concepts", []))
                all_questions.extend(extraction.get("questions", []))
            except Exception as e:
                logger.warning("Chunk %d failed: %s", idx + 1, e)
                continue

        return {
            "raw_text": cleaned_text,
            "page_count": pdf_metadata.get("page_count", 0),
            "concepts_extracted": len(all_concepts),
            "questions_generated": len(all_questions),
            "chunks_processed": len(chunks),
        }

    def _process_image(
        self,
        doc_id: int,
        file_path: Path,
        subject_id: int,
        metadata: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Process an image with OCR.

        Args:
            doc_id: Document ID.
            file_path: Image file path.
            subject_id: Subject ID.
            metadata: Additional metadata.

        Returns:
            Processing result.
        """
        logger.info("Processing image: %s (doc_id=%d)", file_path.name, doc_id)

        image_type = metadata.get("image_type", "printed") if metadata else "printed"
        ocr_text = self.ocr_processor.extract_text(file_path, image_type=image_type)

        if not ocr_text or len(ocr_text.strip()) < 10:
            logger.warning("OCR produced minimal text for %s", file_path.name)
            return {"raw_text": ocr_text, "concepts_extracted": 0}

        # Process extracted text with LLM
        cleaned = self.text_processor.clean_text(ocr_text)
        chunks = self.text_processor.chunk_text(cleaned)

        all_concepts: List[Dict[str, Any]] = []
        for chunk in chunks:
            try:
                extraction = self._extract_knowledge(chunk, subject_id)
                all_concepts.extend(extraction.get("concepts", []))
            except Exception as e:
                logger.warning("Chunk processing failed: %s", e)

        return {
            "raw_text": cleaned,
            "ocr_text": ocr_text,
            "concepts_extracted": len(all_concepts),
        }

    def _process_audio(
        self,
        doc_id: int,
        file_path: Path,
        subject_id: int,
        metadata: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Process an audio file with Whisper.

        Args:
            doc_id: Document ID.
            file_path: Audio file path.
            subject_id: Subject ID.
            metadata: Additional metadata.

        Returns:
            Processing result.
        """
        logger.info("Processing audio: %s (doc_id=%d)", file_path.name, doc_id)

        # Initialize transcriber if needed
        if self.stt_transcriber is None:
            try:
                self.stt_transcriber = WhisperTranscriber()
            except Exception as e:
                logger.warning("Whisper model not available: %s", e)
                return {"raw_text": "", "transcription_error": str(e)}

        # Transcribe
        transcription = self.stt_transcriber.transcribe(file_path)
        transcript_text = transcription.get("text", "")

        if not transcript_text:
            return {"raw_text": "", "concepts_extracted": 0}

        # Process transcript with LLM
        cleaned = self.text_processor.clean_text(transcript_text)
        chunks = self.text_processor.chunk_text(cleaned)

        all_concepts: List[Dict[str, Any]] = []
        for chunk in chunks:
            try:
                extraction = self._extract_knowledge(chunk, subject_id)
                all_concepts.extend(extraction.get("concepts", []))
            except Exception as e:
                logger.warning("Chunk processing failed: %s", e)

        return {
            "raw_text": cleaned,
            "transcript": transcript_text,
            "duration_seconds": transcription.get("duration", 0),
            "concepts_extracted": len(all_concepts),
        }

    def _process_text(
        self,
        doc_id: int,
        file_path: Path,
        subject_id: int,
        metadata: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Process a plain text file.

        Args:
            doc_id: Document ID.
            file_path: Text file path.
            subject_id: Subject ID.
            metadata: Additional metadata.

        Returns:
            Processing result.
        """
        logger.info("Processing text: %s (doc_id=%d)", file_path.name, doc_id)

        with open(file_path, "r", encoding="utf-8") as f:
            raw_text = f.read()

        cleaned = self.text_processor.clean_text(raw_text)
        chunks = self.text_processor.chunk_text(cleaned)

        all_concepts: List[Dict[str, Any]] = []
        for chunk in chunks:
            try:
                extraction = self._extract_knowledge(chunk, subject_id)
                all_concepts.extend(extraction.get("concepts", []))
            except Exception as e:
                logger.warning("Chunk processing failed: %s", e)

        return {
            "raw_text": cleaned,
            "concepts_extracted": len(all_concepts),
        }

    def _extract_knowledge(self, text: str, subject_id: int) -> Dict[str, Any]:
        """Extract concepts and questions from text using LLM.

        Args:
            text: Text chunk to process.
            subject_id: Subject ID.

        Returns:
            Dict with 'concepts' and 'questions' lists.
        """
        prompt = self._build_extraction_prompt(text)
        system_prompt = (
            "You are an expert educational content analyzer. "
            "Extract key concepts, definitions, and generate quiz questions. "
            "Always respond with valid JSON."
        )

        try:
            raw_json = self.llm_engine.extract_json(
                prompt=prompt,
                system_prompt=system_prompt,
            )
            return self.json_parser.parse_extraction_output(raw_json)
        except Exception as e:
            logger.error("Knowledge extraction failed: %s", e)
            return {"concepts": [], "questions": []}

    def _build_extraction_prompt(self, text: str) -> str:
        """Build the LLM prompt for concept extraction.

        Args:
            text: Text to analyze.

        Returns:
            Prompt string.
        """
        return f"""Analyze the following educational text and extract structured knowledge.

Text:
{text}

Extract:
1. Key concepts with definitions (term, definition, importance: high/medium/low, related concepts)
2. Topics covered
3. Quiz questions (multiple choice with 4 options, or true/false, or short answer)

Respond with JSON in this exact format:
{{
  "concepts": [
    {{
      "term": "Concept Name",
      "definition": "Clear definition of the concept",
      "importance": "high",
      "related_concepts": ["Related Concept 1", "Related Concept 2"]
    }}
  ],
  "topics": [
    {{
      "name": "Topic Name",
      "description": "Brief description"
    }}
  ],
  "questions": [
    {{
      "question": "What is...?",
      "answer": "Correct answer",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "type": "multiple_choice",
      "difficulty": "medium"
    }}
  ]
}}

Ensure all JSON is valid. Include at least 2-3 concepts if the text contains educational content."""
