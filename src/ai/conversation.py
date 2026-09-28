"""Conversation manager for NeuroNote AI chat sessions."""

from __future__ import annotations

from typing import Any

from src.database.repository import get_chat_history, save_chat_message
from src.utils.logging import setup_logging

logger = setup_logging(__name__)


class ConversationManager:
    """Manages chat conversation history and sessions.

    Stores:
    - Question
    - Answer
    - Timestamp
    - Document reference
    - Source pages
    """

    def __init__(self, db_path: Any = None) -> None:
        self.db_path = db_path

    def save_message(
        self,
        session_id: str,
        document_id: int,
        role: str,
        message: str,
        context_chunks: str | None = None,
        source_page: int | None = None,
        confidence: float | None = None,
    ) -> int:
        """Save a chat message to the database.

        Args:
            session_id: Chat session identifier.
            document_id: Related document ID.
            role: 'user' or 'assistant'.
            message: Message text.
            context_chunks: Optional context used.
            source_page: Optional source page reference.
            confidence: Optional confidence score.

        Returns:
            Message ID.
        """
        return save_chat_message(
            document_id=document_id,
            session_id=session_id,
            role=role,
            message=message,
            context_chunks=context_chunks,
            source_page=source_page,
            confidence=confidence,
            db_path=self.db_path,
        )

    def load_history(self, session_id: str, limit: int = 50) -> list[dict[str, Any]]:
        """Load chat history for a session.

        Args:
            session_id: Session identifier.
            limit: Maximum messages to load.

        Returns:
            List of message dicts.
        """
        return get_chat_history(session_id, limit=limit, db_path=self.db_path)

    def get_recent_sessions(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent conversation sessions.

        Args:
            limit: Maximum sessions to return.

        Returns:
            List of session summary dicts.
        """
        try:
            from src.database.connection import get_db

            with get_db() as conn:
                rows = conn.execute(
                    """SELECT session_id, document_id, MIN(created_at) as first_msg,
                              MAX(created_at) as last_msg, COUNT(*) as msg_count
                       FROM chat_history
                       GROUP BY session_id
                       ORDER BY last_msg DESC
                       LIMIT ?""",
                    (limit,),
                ).fetchall()

                sessions = []
                for row in rows:
                    sessions.append(
                        {
                            "session_id": row["session_id"],
                            "document_id": row["document_id"],
                            "first_message": row["first_msg"],
                            "last_message": row["last_msg"],
                            "message_count": row["msg_count"],
                        }
                    )
                return sessions
        except Exception as exc:
            logger.error("Failed to get recent sessions: %s", exc)
            return []

    def get_session_title(self, session_id: str) -> str:
        """Generate a title for a session based on first question.

        Args:
            session_id: Session identifier.

        Returns:
            Session title string.
        """
        history = self.load_history(session_id, limit=1)
        if history:
            first_msg = history[0].get("message", "")
            return first_msg[:50] + "..." if len(first_msg) > 50 else first_msg
        return f"Chat {session_id[:8]}"

    def clear_session(self, session_id: str) -> bool:
        """Clear all messages for a session.

        Args:
            session_id: Session identifier.

        Returns:
            True if cleared successfully.
        """
        try:
            from src.database.connection import get_db

            with get_db() as conn:
                conn.execute("DELETE FROM chat_history WHERE session_id = ?", (session_id,))
            logger.info("Cleared chat session %s", session_id)
            return True
        except Exception as exc:
            logger.error("Failed to clear session %s: %s", session_id, exc)
            return False

    def clear_all_sessions(self) -> bool:
        """Clear all chat sessions.

        Returns:
            True if cleared successfully.
        """
        try:
            from src.database.connection import get_db

            with get_db() as conn:
                conn.execute("DELETE FROM chat_history")
            logger.info("Cleared all chat sessions")
            return True
        except Exception as exc:
            logger.error("Failed to clear all sessions: %s", exc)
            return False

    def get_conversation_context(self, session_id: str, max_messages: int = 6) -> str:
        """Build conversation context from recent history.

        Args:
            session_id: Session identifier.
            max_messages: Number of recent messages to include.

        Returns:
            Formatted conversation context string.
        """
        history = self.load_history(session_id, limit=max_messages)
        if not history:
            return ""

        parts = []
        for msg in history[-max_messages:]:
            role = msg.get("role", "user")
            text = msg.get("message", "")
            prefix = "Student" if role == "user" else "Tutor"
            parts.append(f"{prefix}: {text[:200]}")

        return "\n".join(parts)
