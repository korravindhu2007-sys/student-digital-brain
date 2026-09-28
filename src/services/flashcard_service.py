"""Flashcard service for NeuroNote."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from src.database.repository import (
    get_flashcards_for_document,
    save_flashcard,
    save_flashcards_bulk,
    update_flashcard_status,
)
from src.llm.ollama import ollama_generate_json
from src.retrieval.retrieval_engine import RetrievalEngine
from src.services.cache_service import get_cache_service
from src.utils.logging import setup_logging

logger = setup_logging(__name__)


@dataclass
class FlashCard:
    """Flashcard structure."""
    id: Optional[int] = None
    document_id: int = 0
    question: str = ""
    answer: str = ""
    example: str = ""
    difficulty: str = "medium"
    page_reference: Optional[int] = None
    learned: bool = False
    for_revision: bool = False


class FlashcardService:
    """Service for flashcard generation and management."""

    def __init__(self, db_path: Optional[Any] = None) -> None:
        self.db_path = db_path
        self.retrieval_engine = RetrievalEngine(db_path)
        self.cache_service = get_cache_service()

    def generate_flashcards(self, document_id: int, count: int = 20) -> list[dict[str, Any]]:
        """Generate flashcards from document chunks.

        Args:
            document_id: Document ID.
            count: Number of flashcards to generate.

        Returns:
            List of flashcard dicts.
        """
        start_time = logger.info("Generating flashcards for document %d", document_id)

        try:
            # Check cache
            cache_key = f"flashcards-{document_id}-{count}"
            cached = self.cache_service.lookup(cache_key, cache_type="flashcards")
            if cached:
                logger.info("Cache hit for flashcards")
                return cached.get("cards", [])

            # Retrieve chunks for flashcards
            retrieval_result = self.retrieval_engine.retrieve_for_flashcards(document_ids=[document_id])
            chunks = retrieval_result.get("chunks", [])

            if not chunks:
                logger.warning("No chunks found for document %d", document_id)
                return []

            # Generate flashcards from chunks
            cards = self._generate_from_chunks(chunks, count, document_id)

            # Save to database
            save_flashcards_bulk(document_id, cards, db_path=self.db_path)

            execution_time = (datetime.now() - start_time).total_seconds()
            logger.info("Generated %d flashcards in %.2f seconds", len(cards), execution_time)

            # Cache result
            self.cache_service.store(cache_key, {"cards": cards}, cache_type="flashcards",
                                   document_ids=[document_id])

            return cards

        except Exception as exc:
            logger.exception("Flashcard generation failed")
            return []

    def shuffle_cards(self, cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Shuffle flashcards.

        Args:
            cards: List of flashcards.

        Returns:
            Shuffled list of flashcards.
        """
        shuffled = cards.copy()
        random.shuffle(shuffled)
        logger.info("Shuffled %d flashcards", len(shuffled))
        return shuffled

    def mark_learned(self, card_id: int, learned: bool = True) -> bool:
        """Mark flashcard as learned.

        Args:
            card_id: Flashcard ID.
            learned: Learned status.

        Returns:
            True if successful.
        """
        try:
            update_flashcard_status(card_id, learned=learned, db_path=self.db_path)
            logger.info("Marked card %d as learned=%s", card_id, learned)
            return True
        except Exception as exc:
            logger.error("Failed to mark card learned: %s", exc)
            return False

    def mark_revision(self, card_id: int, for_revision: bool = True) -> bool:
        """Mark flashcard for revision.

        Args:
            card_id: Flashcard ID.
            for_revision: Revision flag.

        Returns:
            True if successful.
        """
        try:
            update_flashcard_status(card_id, for_revision=for_revision, db_path=self.db_path)
            logger.info("Marked card %d for revision=%s", card_id, for_revision)
            return True
        except Exception as exc:
            logger.error("Failed to mark card for revision: %s", exc)
            return False

    def load_flashcards(self, document_id: int, learned: Optional[bool] = None) -> list[dict[str, Any]]:
        """Load flashcards for a document.

        Args:
            document_id: Document ID.
            learned: Optional learned filter.

        Returns:
            List of flashcard dicts.
        """
        return get_flashcards_for_document(document_id, learned=learned, db_path=self.db_path)

    def save_flashcards(self, document_id: int, cards: list[dict[str, Any]]) -> bool:
        """Save flashcards to database.

        Args:
            document_id: Document ID.
            cards: List of flashcard dicts.

        Returns:
            True if successful.
        """
        try:
            save_flashcards_bulk(document_id, cards, db_path=self.db_path)
            logger.info("Saved %d flashcards for document %d", len(cards), document_id)
            return True
        except Exception as exc:
            logger.error("Failed to save flashcards: %s", exc)
            return False

    def _generate_from_chunks(self, chunks: list[dict[str, Any]], count: int,
                              document_id: int) -> list[dict[str, Any]]:
        """Generate flashcards from chunks."""
        try:
            # Prepare context from chunks
            context_parts = []
            for chunk in chunks[:10]:
                text = chunk.get("text", "")
                page = chunk.get("page_number") or chunk.get("page", "?")
                context_parts.append(f"[Page {page}]\n{text}")

            context = "\n\n".join(context_parts)

            # Use LLM to generate flashcards
            prompt = f"""Generate {count} flashcards from the following study material.
Each flashcard should have a question, answer, example, and difficulty level.

Format each card as JSON:
[
    {{
        "question": "What is...?",
        "answer": "It is...",
        "example": "For instance...",
        "difficulty": "easy|medium|hard",
        "page_reference": 1
    }}
]

Study material:
{context}

Generate exactly {count} flashcards. Return ONLY the JSON array."""

            result_text = ollama_generate_json(prompt)

            if result_text and isinstance(result_text, list):
                cards = []
                for idx, item in enumerate(result_text[:count]):
                    if isinstance(item, dict):
                        card = {
                            "front": item.get("question", ""),
                            "back": item.get("answer", ""),
                            "example": item.get("example", ""),
                            "difficulty": item.get("difficulty", "medium"),
                            "page_reference": item.get("page_reference", chunks[idx % len(chunks)].get("page_number") if chunks else 1),
                            "type": "question",
                        }
                        cards.append(card)
                logger.info("Generated %d flashcards using LLM", len(cards))
                return cards

        except Exception as exc:
            logger.warning("LLM flashcard generation failed: %s", exc)

        # Fallback: create simple flashcards from chunks
        return self._fallback_flashcards(chunks, count, document_id)

    def _fallback_flashcards(self, chunks: list[dict[str, Any]], count: int,
                            document_id: int) -> list[dict[str, Any]]:
        """Create flashcards from chunks without LLM."""
        cards = []
        for idx, chunk in enumerate(chunks[:count]):
            text = chunk.get("text", "")
            words = text.split()
            # Create a simple question from first few words
            question = f"What is described in this section?"
            answer = text[:200] + "..." if len(text) > 200 else text

            card = {
                "front": question,
                "back": answer,
                "example": "",
                "difficulty": "medium",
                "page_reference": chunk.get("page_number") or chunk.get("page", 1),
                "type": "question",
            }
            cards.append(card)

        logger.info("Created %d fallback flashcards", len(cards))
        return cards


# Global service instance
_flashcard_service: Optional[FlashcardService] = None


def get_flashcard_service(db_path: Optional[Any] = None) -> FlashcardService:
    """Get or create flashcard service instance."""
    global _flashcard_service
    if _flashcard_service is None or db_path:
        _flashcard_service = FlashcardService(db_path)
    return _flashcard_service


