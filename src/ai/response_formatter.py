"""Response formatter for NeuroNote AI responses."""

from __future__ import annotations

import json
import re
from typing import Any

from src.utils.logging import setup_logging

logger = setup_logging(__name__)


class ResponseFormatter:
    """Formats AI responses into structured, readable output."""

    @staticmethod
    def parse_ollama_response(response_text: str) -> dict[str, Any]:
        """Parse Ollama JSON response safely.

        Args:
            response_text: Raw response text from Ollama.

        Returns:
            Parsed response dict.
        """
        if not response_text:
            return {
                "answer": "No response was generated.",
                "confidence": 0,
                "related_topics": [],
                "suggested_followups": [],
            }

        # Try to extract JSON from response
        try:
            # Find JSON block
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                return {
                    "answer": str(parsed.get("answer", response_text[:500])),
                    "confidence": int(parsed.get("confidence", 75)),
                    "related_topics": [str(t) for t in parsed.get("related_topics", []) if t],
                    "suggested_followups": [str(f) for f in parsed.get("suggested_followups", []) if f],
                    "source_document": str(parsed.get("source_document", "")),
                    "source_page": parsed.get("source_page"),
                    "source_paragraph": parsed.get("source_paragraph"),
                }
        except (json.JSONDecodeError, KeyError, ValueError, TypeError) as exc:
            logger.warning("Failed to parse Ollama JSON response: %s", exc)

        # Fallback: use raw text
        return {
            "answer": response_text[:1000],
            "confidence": 60,
            "related_topics": [],
            "suggested_followups": ["Explain more", "Give example", "Summarize"],
        }

    @staticmethod
    def format_response(
        answer: str,
        sources: list[dict[str, Any]],
        confidence: int,
        confidence_label: str,
        related_topics: list[str],
        followups: list[str],
        page_numbers: list[int],
    ) -> dict[str, Any]:
        """Build a complete structured response.

        Args:
            answer: The answer text.
            sources: Source citations.
            confidence: Confidence score.
            confidence_label: Confidence label (High/Medium/Low).
            related_topics: Related topic suggestions.
            followups: Follow-up question suggestions.
            page_numbers: Source page numbers.

        Returns:
            Complete response dict.
        """
        return {
            "ok": True,
            "answer": answer,
            "summary": answer[:200] + "..." if len(answer) > 200 else answer,
            "confidence": confidence,
            "confidence_label": confidence_label,
            "related_topics": related_topics[:5],
            "suggested_followups": followups[:6],
            "sources": sources,
            "source_pages": page_numbers,
            "source_document": sources[0].get("source_document", "Unknown") if sources else "Unknown",
        }

    @staticmethod
    def format_no_answer_message(reason: str = "") -> dict[str, Any]:
        """Format a no-answer response.

        Args:
            reason: Reason why answer is not available.

        Returns:
            No-answer response dict.
        """
        message = reason or "The uploaded document does not contain enough information to answer this question."
        return {
            "ok": True,
            "answer": message,
            "summary": message,
            "confidence": 0,
            "confidence_label": "Low",
            "related_topics": [],
            "suggested_followups": ["Upload another PDF", "Ask a different question"],
            "sources": [],
            "source_pages": [],
            "source_document": "",
        }

    @staticmethod
    def format_error_message(error: str) -> dict[str, Any]:
        """Format an error response.

        Args:
            error: Error description.

        Returns:
            Error response dict.
        """
        return {
            "ok": False,
            "answer": f"An error occurred: {error}",
            "summary": "Error processing your request.",
            "confidence": 0,
            "confidence_label": "Low",
            "related_topics": [],
            "suggested_followups": [],
            "sources": [],
            "source_pages": [],
            "source_document": "",
        }

    @staticmethod
    def format_study_notes(parsed: dict[str, Any]) -> dict[str, Any]:
        """Format study notes from parsed Ollama response.

        Args:
            parsed: Parsed response dict.

        Returns:
            Structured study notes.
        """
        return {
            "introduction": parsed.get("introduction", ""),
            "definitions": parsed.get("definitions", []),
            "core_concepts": parsed.get("core_concepts", []),
            "important_points": parsed.get("important_points", []),
            "examples": parsed.get("examples", []),
            "applications": parsed.get("applications", []),
            "algorithms": parsed.get("algorithms", []),
            "formulae": parsed.get("formulae", []),
            "hardware_software": parsed.get("hardware_software", []),
            "summary": parsed.get("summary", ""),
        }

    @staticmethod
    def format_flash_cards(parsed: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Format flash cards from parsed Ollama response.

        Args:
            parsed: List of card dicts.

        Returns:
            Formatted flash cards.
        """
        if not isinstance(parsed, list):
            return []

        cards = []
        for item in parsed[:30]:
            cards.append(
                {
                    "front": str(item.get("front", "")),
                    "back": str(item.get("back", "")),
                    "type": str(item.get("type", "question")),
                    "difficulty": str(item.get("difficulty", "medium")),
                    "page_number": item.get("page_number"),
                }
            )
        return cards

    @staticmethod
    def format_highlights(parsed: dict[str, Any]) -> list[dict[str, Any]]:
        """Format highlights from parsed Ollama response.

        Args:
            parsed: Parsed response dict.

        Returns:
            List of highlight dicts.
        """
        highlights = parsed.get("highlights", [])
        if not isinstance(highlights, list):
            return []

        result = []
        for h in highlights:
            result.append(
                {
                    "type": str(h.get("type", "important")),
                    "text": str(h.get("text", "")),
                    "page_number": h.get("page_number"),
                    "reason": str(h.get("reason", "")),
                }
            )
        return result

    @staticmethod
    def format_formulas(parsed: dict[str, Any]) -> list[dict[str, Any]]:
        """Format formulas from parsed Ollama response.

        Args:
            parsed: Parsed response dict.

        Returns:
            List of formula dicts.
        """
        formulas = parsed.get("formulas", [])
        if not isinstance(formulas, list):
            return []

        result = []
        for f in formulas:
            result.append(
                {
                    "formula": str(f.get("formula", "")),
                    "meaning": str(f.get("meaning", "")),
                    "variables": str(f.get("variables", "")),
                    "where_used": str(f.get("where_used", "")),
                    "example": str(f.get("example", "")),
                    "page_number": f.get("page_number"),
                }
            )
        return result
