"""Formula extraction service for NeuroNote."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from src.database.repository import get_formulas_for_document, save_formula, save_formulas_bulk
from src.llm.ollama import ollama_generate_json
from src.retrieval.retrieval_engine import RetrievalEngine
from src.services.cache_service import get_cache_service
from src.utils.logging import setup_logging

logger = setup_logging(__name__)


@dataclass
class Formula:
    """Formula structure."""
    id: Optional[int] = None
    document_id: int = 0
    formula: str = ""
    meaning: str = ""
    variables: str = ""
    where_used: str = ""
    example: str = ""
    page_number: Optional[int] = None


class FormulaService:
    """Service for formula extraction and management."""

    def __init__(self, db_path: Optional[Any] = None) -> None:
        self.db_path = db_path
        self.retrieval_engine = RetrievalEngine(db_path)
        self.cache_service = get_cache_service()

    def extract_formulas(self, document_id: int) -> list[dict[str, Any]]:
        """Extract formulas from document.

        Args:
            document_id: Document ID.

        Returns:
            List of formula dicts.
        """
        logger.info("Extracting formulas from document %d", document_id)

        # Check for cached formulas
        existing = get_formulas_for_document(document_id, db_path=self.db_path)
        if existing:
            logger.info("Found %d existing formulas", len(existing))
            return existing

        # Retrieve chunks with formulas
        retrieval_result = self.retrieval_engine.retrieve_for_formula(document_ids=[document_id])
        chunks = retrieval_result.get("chunks", [])

        if not chunks:
            logger.info("No formula chunks found, returning empty list")
            return []

        # Extract formulas using LLM
        formulas = self._extract_from_chunks(chunks, document_id)

        if formulas:
            logger.info("Extracted %d formulas", len(formulas))
        else:
            logger.info("No formulas detected in document")

        return formulas

    def extract_equations(self, document_id: int) -> list[dict[str, Any]]:
        """Extract equations from document.

        Args:
            document_id: Document ID.

        Returns:
            List of equation dicts.
        """
        return self.extract_formulas(document_id)

    def extract_syntax(self, document_id: int) -> list[dict[str, Any]]:
        """Extract syntax/formulas from document.

        Args:
            document_id: Document ID.

        Returns:
            List of formula dicts.
        """
        return self.extract_formulas(document_id)

    def generate_formula_sheet(self, document_id: int) -> Dict[str, Any]:
        """Generate formula sheet for document.

        Args:
            document_id: Document ID.

        Returns:
            Dict with formula sheet data.
        """
        start_time = logger.info("Generating formula sheet for document %d", document_id)

        try:
            # Check cache
            cache_key = f"formula-sheet-{document_id}"
            cached = self.cache_service.lookup(cache_key, cache_type="formula")
            if cached:
                logger.info("Cache hit for formula sheet")
                return cached

            # Extract formulas
            formulas = self.extract_formulas(document_id)

            if not formulas:
                result = {
                    "formulas": [],
                    "message": "No formulas were detected.",
                    "count": 0,
                }
            else:
                # Save to database
                self._save_formulas(document_id, formulas)

                result = {
                    "formulas": formulas,
                    "message": f"Found {len(formulas)} formulas.",
                    "count": len(formulas),
                }

            execution_time = (datetime.now() - start_time).total_seconds()
            logger.info("Formula sheet generated in %.2f seconds", execution_time)

            # Cache result
            self.cache_service.store(cache_key, result, cache_type="formula",
                                   document_ids=[document_id])

            return result

        except Exception as exc:
            logger.exception("Formula sheet generation failed")
            return {"formulas": [], "message": f"Error: {exc}", "count": 0}

    def save_formula_sheet(self, document_id: int, formulas: list[dict[str, Any]]) -> bool:
        """Save formula sheet to database.

        Args:
            document_id: Document ID.
            formulas: List of formula dicts.

        Returns:
            True if successful.
        """
        try:
            self._save_formulas(document_id, formulas)
            logger.info("Saved formula sheet for document %d", document_id)
            return True
        except Exception as exc:
            logger.error("Failed to save formula sheet: %s", exc)
            return False

    def get_formulas(self, document_id: int) -> list[dict[str, Any]]:
        """Get formulas for a document.

        Args:
            document_id: Document ID.

        Returns:
            List of formula dicts.
        """
        return get_formulas_for_document(document_id, db_path=self.db_path)

    def _extract_from_chunks(self, chunks: list[dict[str, Any]], document_id: int) -> list[dict[str, Any]]:
        """Extract formulas from chunks using LLM."""
        try:
            # Prepare context
            context_parts = []
            for chunk in chunks[:10]:
                text = chunk.get("text", "")
                page = chunk.get("page_number") or chunk.get("page", "?")
                context_parts.append(f"[Page {page}]\n{text}")

            context = "\n\n".join(context_parts)

            # Use LLM to extract formulas
            prompt = f"""Extract all mathematical formulas, equations, and important expressions from the following study material.

For each formula, provide:
- formula: The exact formula text
- meaning: What the formula means
- variables: Explanation of variables
- where_used: Where this formula is applied
- example: Example usage if available
- page_number: Source page number

Format as JSON array:
[
    {{
        "formula": "E = mc²",
        "meaning": "Mass-energy equivalence",
        "variables": "E=energy, m=mass, c=speed of light",
        "where_used": "Physics calculations",
        "example": "Calculate energy from mass",
        "page_number": 1
    }}
]

If no formulas are found, return an empty array [].

Study material:
{context}

Return ONLY the JSON array."""

            result = ollama_generate_json(prompt)

            if result and isinstance(result, list):
                # Enrich with page references
                formulas = []
                for idx, item in enumerate(result):
                    if isinstance(item, dict):
                        formula = {
                            "formula": item.get("formula", ""),
                            "meaning": item.get("meaning", ""),
                            "variables": item.get("variables", ""),
                            "where_used": item.get("where_used", ""),
                            "example": item.get("example", ""),
                            "page_number": item.get("page_number", chunks[idx % len(chunks)].get("page_number") if chunks else 1),
                        }
                        formulas.append(formula)
                return formulas

        except Exception as exc:
            logger.warning("LLM formula extraction failed: %s", exc)

        # Fallback: simple extraction
        return self._fallback_extraction(chunks)

    def _fallback_extraction(self, chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Simple formula extraction without LLM."""
        formulas = []
        import re

        for chunk in chunks:
            text = chunk.get("text", "")
            # Look for equations (simple pattern)
            equations = re.findall(r'[A-Za-z]\s*=\s*[^.!?\n]{3,50}', text)
            for eq in equations[:5]:
                formulas.append({
                    "formula": eq.strip(),
                    "meaning": "Extracted equation",
                    "variables": "",
                    "where_used": "",
                    "example": "",
                    "page_number": chunk.get("page_number") or chunk.get("page", 1),
                })

        return formulas

    def _save_formulas(self, document_id: int, formulas: list[dict[str, Any]]) -> None:
        """Save formulas to database."""
        save_formulas_bulk(document_id, formulas, db_path=self.db_path)
        logger.info("Saved %d formulas for document %d", len(formulas), document_id)


# Global service instance
_formula_service: Optional[FormulaService] = None


def get_formula_service(db_path: Optional[Any] = None) -> FormulaService:
    """Get or create formula service instance."""
    global _formula_service
    if _formula_service is None or db_path:
        _formula_service = FormulaService(db_path)
    return _formula_service