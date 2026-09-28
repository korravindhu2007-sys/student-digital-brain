"""Citation engine for NeuroNote AI responses.

Every AI answer must include source citations.
"""

from __future__ import annotations

from typing import Any

from src.utils.logging import setup_logging

logger = setup_logging(__name__)


class CitationEngine:
    """Generates source citations for AI responses."""

    @staticmethod
    def build_citations(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Build structured citations from retrieved chunks.

        Args:
            chunks: List of retrieved chunks with source metadata.

        Returns:
            List of citation dicts.
        """
        citations = []
        seen_pages: set[int] = set()

        for chunk in chunks:
            page = chunk.get("page_number") or chunk.get("page", 0)
            if isinstance(page, str):
                try:
                    page = int(page)
                except (ValueError, TypeError):
                    page = 0

            citation = {
                "source_document": chunk.get("source_filename") or chunk.get("filename", "Unknown"),
                "source_page": page,
                "source_paragraph": chunk.get("chunk_number") or chunk.get("chunk_index", 1),
                "text": (chunk.get("text", "") or "")[:250],
            }

            # Avoid duplicate page citations
            page_key = (citation["source_document"], citation["source_page"])
            if page_key not in {(c["source_document"], c["source_page"]) for c in citations}:
                citations.append(citation)
                seen_pages.add(page)

        return citations[:5]  # Max 5 unique citations

    @staticmethod
    def format_citations_markdown(citations: list[dict[str, Any]]) -> str:
        """Format citations as markdown string.

        Args:
            citations: List of citation dicts.

        Returns:
            Markdown formatted citations.
        """
        if not citations:
            return ""

        lines = ["\n\n**Sources:**"]
        for i, citation in enumerate(citations[:3], 1):
            doc = citation.get("source_document", "Unknown")
            page = citation.get("source_page", "?")
            para = citation.get("source_paragraph", "?")
            lines.append(f"{i}. 📄 **{doc}** → Page {page}, Paragraph {para}")

        return "\n".join(lines)

    @staticmethod
    def estimate_confidence(chunks: list[dict[str, Any]]) -> tuple[int, str]:
        """Estimate confidence based on chunk similarity and coverage.

        Args:
            chunks: Retrieved chunks with relevance/scores.

        Returns:
            Tuple of (confidence_score, confidence_label).
        """
        if not chunks:
            return 0, "Low"

        # Calculate average relevance
        total_relevance = 0
        for chunk in chunks:
            relevance = chunk.get("relevance") or chunk.get("confidence", 0)
            if isinstance(relevance, str):
                try:
                    relevance = float(relevance)
                except (ValueError, TypeError):
                    relevance = 50
            total_relevance += float(relevance)

        avg_relevance = total_relevance / len(chunks)

        # Determine label
        if avg_relevance >= 85:
            label = "High"
        elif avg_relevance >= 60:
            label = "Medium"
        else:
            label = "Low"

        return int(avg_relevance), label

    @staticmethod
    def get_page_numbers(chunks: list[dict[str, Any]]) -> list[int]:
        """Get unique page numbers from chunks.

        Args:
            chunks: List of chunks.

        Returns:
            Sorted list of unique page numbers.
        """
        pages: set[int] = set()
        for chunk in chunks:
            page = chunk.get("page_number") or chunk.get("page")
            if page is not None:
                try:
                    pages.add(int(page))
                except (ValueError, TypeError):
                    pass
        return sorted(pages)
