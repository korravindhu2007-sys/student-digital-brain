"""Dashboard service for NeuroNote."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.database.repository import (
    dashboard_counts,
    get_document,
    list_documents,
)
from src.utils.logging import setup_logging

logger = setup_logging(__name__)


@dataclass
class DashboardStats:
    """Dashboard statistics structure."""
    total_documents: int
    completed_documents: int
    total_chunks: int
    total_chats: int
    total_flashcards: int
    total_highlights: int
    total_formulas: int
    storage_used: int
    recent_documents: list[dict[str, Any]]
    recent_chats: list[dict[str, Any]]
    study_statistics: dict[str, Any]
    subjects: list[str]
    topics: list[str]


class DashboardService:
    """Service for dashboard statistics and metrics."""

    def __init__(self, db_path: Optional[Any] = None) -> None:
        self.db_path = db_path

    def dashboard_statistics(self) -> dict[str, Any]:
        """Get dashboard statistics.

        Returns:
            Dict with dashboard stats including:
            - Documents
            - Pages
            - Chunks
            - Flashcards
            - Study Notes
            - Highlights
            - Chat Sessions
        """
        logger.info("Fetching dashboard statistics")

        try:
            # Get document counts
            counts = dashboard_counts(db_path=self.db_path)
            documents = list_documents(status="completed", limit=100, db_path=self.db_path)

            # Calculate totals
            total_documents = counts.get("total", 0)
            completed_documents = counts.get("completed", 0)

            # Get chunks count
            total_chunks = sum(doc.get("chunk_count", 0) for doc in documents)

            # Get subjects and topics
            subjects = sorted({str(doc.get("subject", "General")) for doc in documents})
            topics = sorted({str(doc.get("topic", "General")) for doc in documents})

            # Get recent documents
            recent_docs = documents[:10]

            # Get storage info
            storage_stats = self._get_storage_statistics()

            return {
                "total_documents": total_documents,
                "completed_documents": completed_documents,
                "processing_documents": counts.get("processing", 0),
                "failed_documents": counts.get("failed", 0),
                "total_chunks": total_chunks,
                "total_pages": sum(doc.get("page_count", 0) for doc in documents),
                "subjects": subjects,
                "topics": topics,
                "recent_documents": recent_docs,
                "storage": storage_stats,
                "health": "good" if completed_documents > 0 else "no_documents",
            }

        except Exception as exc:
            logger.exception("Dashboard statistics fetch failed")
            return self._fallback_statistics()

    def recent_documents(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent documents.

        Args:
            limit: Maximum number of documents.

        Returns:
            List of recent document dicts.
        """
        logger.info("Fetching %d recent documents", limit)

        try:
            return list_documents(limit=limit, db_path=self.db_path)
        except Exception as exc:
            logger.error("Failed to fetch recent documents: %s", exc)
            return []

    def recent_chats(self, limit: int = 20, session_id: Optional[str] = None) -> list[dict[str, Any]]:
        """Get recent chat sessions.

        Args:
            limit: Maximum number of chats.
            session_id: Optional session filter.

        Returns:
            List of chat session dicts.
        """
        logger.info("Fetching recent chats")

        try:
            from src.database.connection import get_db

            with get_db() as conn:
                query = """
                    SELECT session_id, document_id, COUNT(*) as message_count,
                           MAX(created_at) as last_message_at
                    FROM chat_history
                """
                params = []

                if session_id:
                    query += " WHERE session_id = ?"
                    params.append(session_id)

                query += """
                    GROUP BY session_id, document_id
                    ORDER BY last_message_at DESC
                    LIMIT ?
                """
                params.append(limit)

                cursor = conn.execute(query, params)
                results = [dict(row) for row in cursor.fetchall()]

                # Enrich with document info
                for result in results:
                    doc_id = result.get("document_id")
                    if doc_id:
                        doc = get_document(doc_id, db_path=self.db_path)
                        if doc:
                            result["document_name"] = doc.get("filename", "Unknown")
                            result["subject"] = doc.get("subject", "General")

                return results

        except Exception as exc:
            logger.error("Failed to fetch recent chats: %s", exc)
            return []

    def study_statistics(self, document_id: Optional[int] = None) -> dict[str, Any]:
        """Get study statistics.

        Args:
            document_id: Optional document filter.

        Returns:
            Dict with study statistics.
        """
        logger.info("Fetching study statistics")

        try:
            from src.database.connection import get_db

            with get_db() as conn:
                # Get flashcard stats
                flashcard_query = "SELECT COUNT(*) as count, SUM(learned) as learned FROM flashcards"
                flashcard_params = []

                if document_id:
                    flashcard_query += " WHERE document_id = ?"
                    flashcard_params.append(document_id)

                cursor = conn.execute(flashcard_query, flashcard_params)
                flashcard_stats = dict(cursor.fetchone() or {})

                # Get highlight stats
                highlight_query = "SELECT COUNT(*) as count, highlight_type FROM highlights"
                highlight_params = []

                if document_id:
                    highlight_query += " WHERE document_id = ?"
                    highlight_params.append(document_id)

                highlight_query += " GROUP BY highlight_type"
                cursor = conn.execute(highlight_query, highlight_params)
                highlight_stats = {row["highlight_type"]: row["count"] for row in cursor.fetchall()}

                # Get formula stats
                formula_query = "SELECT COUNT(*) as count FROM formula_sheets"
                formula_params = []

                if document_id:
                    formula_query += " WHERE document_id = ?"
                    formula_params.append(document_id)

                cursor = conn.execute(formula_query, formula_params)
                formula_count = cursor.fetchone()[0] or 0

                return {
                    "flashcards": {
                        "total": flashcard_stats.get("count", 0),
                        "learned": flashcard_stats.get("learned", 0),
                        "unlearned": (flashcard_stats.get("count", 0) - flashcard_stats.get("learned", 0)),
                    },
                    "highlights": {
                        "total": sum(highlight_stats.values()),
                        "by_type": highlight_stats,
                    },
                    "formulas": {
                        "total": formula_count,
                    },
                    "study_notes": {
                        "count": self._count_study_notes(document_id),
                    },
                }

        except Exception as exc:
            logger.error("Failed to fetch study statistics: %s", exc)
            return {
                "flashcards": {"total": 0, "learned": 0, "unlearned": 0},
                "highlights": {"total": 0, "by_type": {}},
                "formulas": {"total": 0},
                "study_notes": {"count": 0},
            }

    def storage_statistics(self) -> dict[str, Any]:
        """Get storage statistics.

        Returns:
            Dict with storage stats.
        """
        logger.info("Fetching storage statistics")

        try:
            return self._get_storage_statistics()
        except Exception as exc:
            logger.error("Failed to fetch storage statistics: %s", exc)
            return {
                "database_size": 0,
                "upload_dir_size": 0,
                "cache_dir_size": 0,
                "total_size": 0,
            }

    def _get_storage_statistics(self) -> dict[str, Any]:
        """Get storage statistics."""
        try:
            from src.config import config

            # Database size
            db_path = config.database.path
            db_size = Path(db_path).stat().st_size if Path(db_path).exists() else 0

            # Upload directory size
            upload_size = self._get_directory_size(config.upload_dir)

            # Cache directory size
            cache_size = self._get_directory_size(config.cache_dir)

            return {
                "database_size": db_size,
                "upload_dir_size": upload_size,
                "cache_dir_size": cache_size,
                "total_size": db_size + upload_size + cache_size,
            }

        except Exception as exc:
            logger.error("Failed to calculate storage: %s", exc)
            return {
                "database_size": 0,
                "upload_dir_size": 0,
                "cache_dir_size": 0,
                "total_size": 0,
            }

    def _get_directory_size(self, directory: Path) -> int:
        """Get total size of directory."""
        total = 0
        if directory.exists():
            for item in directory.rglob("*"):
                if item.is_file():
                    total += item.stat().st_size
        return total

    def _count_study_notes(self, document_id: Optional[int] = None) -> int:
        """Count study notes."""
        try:
            from src.database.connection import get_db

            with get_db() as conn:
                query = "SELECT COUNT(*) FROM study_notes"
                params = []

                if document_id:
                    query += " WHERE document_id = ?"
                    params.append(document_id)

                cursor = conn.execute(query, params)
                result = cursor.fetchone()
                return result[0] if result else 0

        except Exception:
            return 0

    def _fallback_statistics(self) -> dict[str, Any]:
        """Fallback statistics when database unavailable."""
        return {
            "total_documents": 0,
            "completed_documents": 0,
            "processing_documents": 0,
            "failed_documents": 0,
            "total_chunks": 0,
            "total_pages": 0,
            "subjects": [],
            "topics": [],
            "recent_documents": [],
            "storage": {
                "database_size": 0,
                "upload_dir_size": 0,
                "cache_dir_size": 0,
                "total_size": 0,
            },
            "health": "error",
        }


# Global service instance
_dashboard_service: Optional[DashboardService] = None


def get_dashboard_service(db_path: Optional[Any] = None) -> DashboardService:
    """Get or create dashboard service instance."""
    global _dashboard_service
    if _dashboard_service is None or db_path:
        _dashboard_service = DashboardService(db_path)
    return _dashboard_service