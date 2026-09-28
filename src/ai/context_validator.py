"""Context validation for hallucination prevention."""

from __future__ import annotations

from typing import Any

from src.utils.logging import setup_logging

logger = setup_logging(__name__)


class ContextValidator:
    """Validates context before sending to Ollama.

    Ensures:
    - Context is not empty
    - Question is meaningful
    - Document exists
    - Chunks exist
    - Never calls Ollama unnecessarily.
    """

    @staticmethod
    def validate_question(question: str | None) -> str | None:
        """Validate and clean user question.

        Args:
            question: Raw question from user.

        Returns:
            Cleaned question or None if invalid.
        """
        if not question:
            return None

        cleaned = question.strip()
        if len(cleaned) < 2:
            return None

        # Sanitize: remove excessive whitespace, truncate
        cleaned = " ".join(cleaned.split())
        if len(cleaned) > 2000:
            cleaned = cleaned[:2000]

        return cleaned

    @staticmethod
    def validate_context(context: str | None) -> tuple[bool, str]:
        """Validate retrieved context before Ollama call.

        Args:
            context: Retrieved context string.

        Returns:
            Tuple of (is_valid, error_message).
        """
        if not context:
            return False, "The uploaded document does not contain enough information to answer this question."

        stripped = context.strip()
        if not stripped:
            return False, "No relevant information was found in the uploaded document."

        if len(stripped) < 10:
            return False, "The uploaded document does not contain enough information to answer this question."

        return True, ""

    @staticmethod
    def validate_chunks(chunks: list[dict[str, Any]] | None) -> tuple[bool, str]:
        """Validate retrieved chunks.

        Args:
            chunks: List of retrieved chunks.

        Returns:
            Tuple of (is_valid, error_message).
        """
        if not chunks:
            return False, "No relevant information was found in the uploaded document."

        if len(chunks) == 0:
            return False, "No relevant information was found in the uploaded document."

        return True, ""

    @staticmethod
    def validate_document_exists(document_ids: list[int] | None) -> bool:
        """Check if document exists in database.

        Args:
            document_ids: List of document IDs.

        Returns:
            True if at least one document exists.
        """
        if not document_ids:
            # No specific document filter - assume documents might exist
            return True

        try:
            from src.database.repository import list_documents

            docs = list_documents()
            doc_ids = {d.get("id") for d in docs}
            return any(did in doc_ids for did in document_ids)
        except Exception:
            return False

    @staticmethod
    def validate_all(
        question: str | None,
        context: str | None,
        chunks: list[dict[str, Any]] | None,
    ) -> tuple[bool, str]:
        """Run all validations before Ollama call.

        Args:
            question: User question.
            context: Retrieved context.
            chunks: Retrieved chunks.

        Returns:
            Tuple of (all_valid, error_message).
        """
        # Validate question
        question_result = ContextValidator.validate_question(question)
        if question_result is None:
            return False, "Please enter a valid question."

        # Validate context
        context_valid, context_error = ContextValidator.validate_context(context)
        if not context_valid:
            logger.warning("Context validation failed: %s", context_error)
            return False, context_error

        # Validate chunks
        chunks_valid, chunks_error = ContextValidator.validate_chunks(chunks)
        if not chunks_valid:
            logger.warning("Chunk validation failed: %s", chunks_error)
            return False, chunks_error

        return True, ""
