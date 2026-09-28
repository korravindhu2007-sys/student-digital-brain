"""Backend service facade for NeuroNote.

Provides a clean API for frontend pages to consume backend services.
"""

from __future__ import annotations

from typing import Any

from src.services import (
    get_chat_service,
    get_dashboard_service,
    get_document_service,
)

__all__ = [
    "get_app_status",
    "get_dashboard_stats",
    "get_dashboard_data",
    "get_pdf_options",
    "process_document",
    "answer_question",
    "get_chat_history",
    "clear_chat_history",
    "get_app_analytics",
]


def get_app_status() -> dict[str, object]:
    """Get application status."""
    return {
        "mode": "Offline-first",
        "backend": "Ollama + SQLite",
        "last_sync": "Local only",
        "storage": "Local workspace",
        "database": True,
        "ollama": True,
    }


def get_dashboard_data() -> dict[str, Any]:
    """Get dashboard statistics."""
    return get_dashboard_stats()


def process_document(file: Any, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    """Process uploaded document through service layer."""
    service = get_document_service()
    result = service.process_document(file, metadata)
    return {
        "ok": result.success,
        "status": result.status,
        "document_id": result.document_id,
        "chunk_count": result.chunk_count,
        "page_count": result.page_count,
        "extracted_chars": result.extracted_chars,
        "cache_hit": result.cache_hit,
        "error": result.error,
    }


def get_dashboard_stats() -> dict[str, Any]:
    """Get dashboard statistics from service layer."""
    service = get_dashboard_service()
    return service.dashboard_statistics()


def get_pdf_options() -> dict[str, Any]:
    """Get PDF document options."""
    from src.database.repository import list_documents

    try:
        documents = [row for row in list_documents() if row.get("source_type") == "pdf"]
        subjects = sorted({str(row.get("subject", "General")) for row in documents})
        topics_by_subject: dict[str, list[str]] = {}
        for row in documents:
            subject = str(row.get("subject", "General"))
            topic = str(row.get("topic", "General"))
            topics_by_subject.setdefault(subject, [])
            if topic not in topics_by_subject[subject]:
                topics_by_subject[subject].append(topic)
        return {
            "subjects": subjects,
            "topics_by_subject": {key: sorted(values) for key, values in topics_by_subject.items()},
            "documents": documents,
        }
    except Exception:
        return {"subjects": [], "topics_by_subject": {}, "documents": []}


def answer_question(question: str, document_ids: list[int] | None = None) -> dict[str, Any]:
    """Answer question using legacy chat service."""
    from src.services.chat_service import get_chat_service
    service = get_chat_service()
    response = service.ask(question, document_ids=document_ids)
    return {
        "ok": True,
        "answer": response.answer,
        "sources": response.sources,
        "confidence": response.confidence,
        "related_topics": response.related_topics,
        "suggested_followups": response.suggested_followups,
        "cache_hit": response.cache_hit,
    }


def get_chat_history(session_id: str = "default", limit: int = 50) -> list[dict[str, Any]]:
    """Get chat history for a session."""
    from src.services.chat_service import get_chat_service
    service = get_chat_service()
    return service.get_history(session_id, limit=limit)


def clear_chat_history(session_id: str = "default") -> bool:
    """Clear chat history for a session."""
    from src.services.chat_service import get_chat_service
    service = get_chat_service()
    return service.clear_history(session_id)


def get_app_analytics() -> dict[str, Any]:
    """Get basic application analytics.

    Returns:
        Dict with analytics data.
    """
    try:
        from src.database.connection import get_db

        with get_db() as conn:
            total_docs = conn.execute("SELECT COUNT(*) as count FROM documents").fetchone()["count"]

        return {
            "total_questions": 0,
            "total_chunks": 0,
            "total_documents": total_docs,
        }
    except Exception:
        return {
            "total_questions": 0,
            "total_chunks": 0,
            "total_documents": 0,
        }