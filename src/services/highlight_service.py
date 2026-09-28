"""Highlight extraction service for NeuroNote."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.database.repository import get_highlights_for_document, save_highlight
from src.llm.ollama import ollama_generate_json
from src.retrieval.retrieval_engine import RetrievalEngine
from src.services.cache_service import get_cache_service
from src.utils.logging import setup_logging

logger = setup_logging(__name__)


@dataclass
class Highlight:
    """Highlight structure."""
    id: Optional[int] = None
    document_id: int = 0
    chunk_id: Optional[int] = None
    highlight_type: str = "important"
    text: str = ""
    page_number: Optional[int] = None
    section_heading: Optional[str] = None
    context: Optional[str] = None
    reason: str = ""


class HighlightService:
    """Service for extracting and managing highlights."""

    def __init__(self, db_path: Optional[Any] = None) -> None:
        self.db_path = db_path
        self.retrieval_engine = RetrievalEngine(db_path)
        self.cache_service = get_cache_service()

    def extract_highlights(self, document_id: int) -> list[dict[str, Any]]:
        """Extract highlights from document.

        Identifies:
            - Definitions
            - Important Lines
            - Algorithms
            - Formulae
            - Exam Tips

        Args:
            document_id: Document ID.

        Returns:
            List of highlight dicts.
        """
        start_time = logger.info("Extracting highlights for document %d", document_id)

        try:
            # Check cache
            cache_key = f"highlights-{document_id}"
            cached = self.cache_service.lookup(cache_key, cache_type="highlights")
            if cached:
                logger.info("Cache hit for highlights")
                return cached.get("highlights", [])

            # Retrieve chunks
            retrieval_result = self.retrieval_engine.retrieve_for_study(document_ids=[document_id])
            chunks = retrieval_result.get("chunks", [])

            if not chunks:
                logger.warning("No chunks found for document %d", document_id)
                return []

            # Extract highlights using LLM
            highlights = self._extract_from_chunks(chunks, document_id)

            # Save to database
            saved_count = self._save_highlights(document_id, highlights)

            execution_time = (datetime.now() - start_time).total_seconds()
            logger.info("Extracted %d highlights in %.2f seconds", saved_count, execution_time)

            # Cache result
            self.cache_service.store(cache_key, {"highlights": highlights}, cache_type="highlights",
                                   document_ids=[document_id])

            return highlights

        except Exception as exc:
            logger.exception("Highlight extraction failed")
            return []

    def highlight_pdf(self, document_id: int) -> list[dict[str, Any]]:
        """Generate highlights for PDF.

        Args:
            document_id: Document ID.

        Returns:
            List of highlight dicts with page references.
        """
        # Same as extract_highlights but focused on PDF format
        return self.extract_highlights(document_id)

    def save_highlights(self, document_id: int, highlights: list[dict[str, Any]]) -> bool:
        """Save highlights to database.

        Args:
            document_id: Document ID.
            highlights: List of highlight dicts.

        Returns:
            True if successful.
        """
        try:
            self._save_highlights(document_id, highlights)
            logger.info("Saved %d highlights for document %d", len(highlights), document_id)
            return True
        except Exception as exc:
            logger.error("Failed to save highlights: %s", exc)
            return False

    def load_highlights(self, document_id: int, highlight_type: Optional[str] = None) -> list[dict[str, Any]]:
        """Load highlights from database.

        Args:
            document_id: Document ID.
            highlight_type: Optional type filter.

        Returns:
            List of highlight dicts.
        """
        return get_highlights_for_document(document_id, highlight_type=highlight_type, db_path=self.db_path)

    def _extract_from_chunks(self, chunks: list[dict[str, Any]], document_id: int) -> list[dict[str, Any]]:
        """Extract highlights from chunks using LLM."""
        try:
            # Prepare context
            context_parts = []
            for chunk in chunks[:15]:
                text = chunk.get("text", "")
                page = chunk.get("page_number") or chunk.get("page", "?")
                context_parts.append(f"[Page {page}]\n{text}")

            context = "\n\n".join(context_parts)

            # Use LLM to extract highlights
            prompt = f"""Extract important highlights from the following study material.
Identify:
1. Definitions (key terms and their meanings)
2. Important Lines (critical statements)
3. Algorithms (step-by-step procedures)
4. Formulae (mathematical expressions)
5. Exam Tips (important points for exams)

For each highlight, provide:
- highlight_type: one of ["definition", "important", "algorithm", "formula", "exam_tip"]
- text: The exact highlighted text
- reason: Why this is important
- page_number: Source page number

Format as JSON array:
[
    {{
        "highlight_type": "definition",
        "text": "Machine Learning is a subset of AI",
        "reason": "Core definition",
        "page_number": 1
    }}
]

Study material:
{context}

Return ONLY the JSON array. Extract at least 10 highlights."""

            result = ollama_generate_json(prompt)

            if result and isinstance(result, list):
                highlights = []
                for item in result:
                    if isinstance(item, dict):
                        highlight = {
                            "highlight_type": item.get("highlight_type", "important"),
                            "text": item.get("text", ""),
                            "reason": item.get("reason", ""),
                            "page_number": item.get("page_number"),
                            "section_heading": None,
                            "context": None,
                        }
                        highlights.append(highlight)
                return highlights

        except Exception as exc:
            logger.warning("LLM highlight extraction failed: %s", exc)

        # Fallback: extract simple highlights
        return self._fallback_highlights(chunks)

    def _fallback_highlights(self, chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Simple highlight extraction without LLM."""
        highlights = []

        # Highlight patterns
        definition_keywords = ["is defined as", "refers to", "means", "definition:", "defined as"]
        important_keywords = ["important", "key", "critical", "essential", "note that", "remember"]
        formula_keywords = ["=", "formula", "equation", "calculated as"]

        for chunk in chunks[:20]:
            text = chunk.get("text", "")
            page = chunk.get("page_number") or chunk.get("page", 1)

            # Check for definitions
            for keyword in definition_keywords:
                if keyword.lower() in text.lower():
                    highlights.append({
                        "highlight_type": "definition",
                        "text": text[:200],
                        "reason": "Contains definition",
                        "page_number": page,
                    })
                    break

            # Check for important lines
            for keyword in important_keywords:
                if keyword.lower() in text.lower():
                    highlights.append({
                        "highlight_type": "important",
                        "text": text[:200],
                        "reason": "Important statement",
                        "page_number": page,
                    })
                    break

            # Check for formulas
            if any(kw in text for kw in formula_keywords):
                highlights.append({
                    "highlight_type": "formula",
                    "text": text[:200],
                    "reason": "Contains formula/equation",
                    "page_number": page,
                })

        return highlights[:20]  # Limit highlights

    def _save_highlights(self, document_id: int, highlights: list[dict[str, Any]]) -> int:
        """Save highlights to database."""
        count = 0
        for highlight in highlights:
            try:
                save_highlight(
                    document_id=document_id,
                    highlight_type=highlight.get("highlight_type", "important"),
                    text=highlight.get("text", ""),
                    page_number=highlight.get("page_number"),
                    section_heading=highlight.get("section_heading"),
                    context=highlight.get("context"),
                    db_path=self.db_path,
                )
                count += 1
            except Exception as exc:
                logger.warning("Failed to save highlight: %s", exc)

        return count


# Global service instance
_highlight_service: Optional[HighlightService] = None


def get_highlight_service(db_path: Optional[Any] = None) -> HighlightService:
    """Get or create highlight service instance."""
    global _highlight_service
    if _highlight_service is None or db_path:
        _highlight_service = HighlightService(db_path)
    return _highlight_service
