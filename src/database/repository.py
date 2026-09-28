"""Repository layer for NeuroNote database operations."""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.database.connection import get_db
from src.utils.logging import setup_logging

logger = setup_logging(__name__)


# ──────────────────────────────────────────────
# Documents
# ──────────────────────────────────────────────


def create_document(
    title: str,
    file_type: str,
    file_path: str,
    file_size: int,
    subject: str = "General",
    topic: str = "General",
    pdf_hash: Optional[str] = None,
    page_count: int = 0,
    raw_text: Optional[str] = None,
    structured_json: Optional[str] = None,
) -> int:
    """Insert a new document record.

    Args:
        title: Document title.
        file_type: File type ('pdf' only).
        file_path: Path to the uploaded file.
        file_size: File size in bytes.
        subject: Subject name.
        topic: Topic name.
        pdf_hash: SHA256 hash of PDF.
        page_count: Number of pages.
        raw_text: Extracted raw text.
        structured_json: Structured JSON data.

    Returns:
        The new document ID.
    """
    with get_db() as conn:
        cursor = conn.execute(
            """INSERT INTO documents (title, file_type, file_path, file_size,
               subject, topic, pdf_hash, page_count, raw_text, structured_json, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')""",
            (title, file_type, file_path, file_size, subject, topic, pdf_hash, page_count, raw_text, structured_json),
        )
        doc_id = cursor.lastrowid
        logger.info("Created document %d: %s", doc_id, title)
        return doc_id


def update_document_status(
    doc_id: int,
    status: str,
    error_message: Optional[str] = None,
    raw_text: Optional[str] = None,
    structured_json: Optional[str] = None,
) -> None:
    """Update document processing status.

    Args:
        doc_id: Document ID.
        status: New status ('pending', 'processing', 'completed', 'failed').
        error_message: Error details if failed.
        raw_text: Extracted raw text if completed.
        structured_json: Structured JSON data.
    """
    fields = ["status = ?"]
    values: List[Any] = [status]

    if error_message is not None:
        fields.append("error_message = ?")
        values.append(error_message)
    if raw_text is not None:
        fields.append("raw_text = ?")
        values.append(raw_text)
    if structured_json is not None:
        fields.append("structured_json = ?")
        values.append(structured_json)
    if status == "completed":
        fields.append("processed_at = CURRENT_TIMESTAMP")

    values.append(doc_id)
    query = f"UPDATE documents SET {', '.join(fields)} WHERE id = ?"

    with get_db() as conn:
        conn.execute(query, values)
        logger.info("Document %d status updated to '%s'", doc_id, status)


def get_document(doc_id: int) -> Optional[Dict[str, Any]]:
    """Get a single document by ID.

    Args:
        doc_id: Document ID.

    Returns:
        Document dict or None if not found.
    """
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_document_by_hash(pdf_hash: str) -> Optional[Dict[str, Any]]:
    """Get document by PDF hash.

    Args:
        pdf_hash: SHA256 hash.

    Returns:
        Document dict or None if not found.
    """
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM documents WHERE pdf_hash = ?", (pdf_hash,))
        row = cursor.fetchone()
        return dict(row) if row else None


def list_documents(
    subject: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """Get documents with optional filters.

    Args:
        subject: Filter by subject.
        status: Filter by status.
        limit: Maximum results.
        offset: Pagination offset.

    Returns:
        List of document dicts.
    """
    conditions: List[str] = []
    values: List[Any] = []

    if subject:
        conditions.append("subject = ?")
        values.append(subject)
    if status:
        conditions.append("status = ?")
        values.append(status)

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    query = f"SELECT * FROM documents {where} ORDER BY created_at DESC LIMIT ? OFFSET ?"
    values.extend([limit, offset])

    with get_db() as conn:
        cursor = conn.execute(query, values)
        return [dict(row) for row in cursor.fetchall()]


def find_pdf_document(subject: Optional[str], topic: Optional[str]) -> Optional[Dict[str, Any]]:
    """Find a PDF document by subject and topic.

    Args:
        subject: Subject name.
        topic: Topic name.

    Returns:
        Document dict or None if not found.
    """
    conditions = ["file_type = 'pdf'"]
    values: List[Any] = []

    if subject:
        conditions.append("subject = ?")
        values.append(subject)
    if topic:
        conditions.append("topic = ?")
        values.append(topic)

    where = " AND ".join(conditions)
    query = f"SELECT * FROM documents WHERE {where} ORDER BY created_at DESC LIMIT 1"

    with get_db() as conn:
        cursor = conn.execute(query, values)
        row = cursor.fetchone()
        return dict(row) if row else None


def latest_pdf_document() -> Optional[Dict[str, Any]]:
    """Get the most recently uploaded PDF document.

    Returns:
        Document dict or None if not found.
    """
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT * FROM documents WHERE file_type = 'pdf' ORDER BY created_at DESC LIMIT 1"
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def dashboard_counts() -> Dict[str, int]:
    """Get document counts for dashboard.

    Returns:
        Dict with document counts.
    """
    with get_db() as conn:
        cursor = conn.execute(
            """SELECT status, COUNT(*) as count FROM documents
               WHERE file_type = 'pdf' GROUP BY status"""
        )
        counts = {row["status"]: row["count"] for row in cursor.fetchall()}
    return {
        "total": sum(counts.values()),
        "completed": counts.get("completed", 0),
        "processing": counts.get("processing", 0),
        "failed": counts.get("failed", 0),
    }


# ──────────────────────────────────────────────
# Chunks
# ──────────────────────────────────────────────


def save_chunks(document_id: int, chunks: List[Dict[str, Any]]) -> None:
    """Save text chunks for a document.

    Args:
        document_id: Document ID.
        chunks: List of chunk dicts with text, page_number, section_heading.
    """
    with get_db() as conn:
        for index, chunk in enumerate(chunks):
            conn.execute(
                """INSERT INTO chunks (document_id, chunk_index, text,
                   page_number, section_heading, token_count)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    document_id,
                    index,
                    chunk.get("text", ""),
                    chunk.get("page_number"),
                    chunk.get("section_heading"),
                    chunk.get("token_count", 0),
                ),
            )
        logger.info("Saved %d chunks for document %d", len(chunks), document_id)


def get_chunks_for_document(document_id: int) -> List[Dict[str, Any]]:
    """Get all chunks for a document.

    Args:
        document_id: Document ID.

    Returns:
        List of chunk dicts.
    """
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT * FROM chunks WHERE document_id = ? ORDER BY chunk_index",
            (document_id,),
        )
        return [dict(row) for row in cursor.fetchall()]


def search_chunks_fts(query: str, document_ids: Optional[List[int]] = None, limit: int = 10) -> List[Dict[str, Any]]:
    """Search chunks using FTS5.

    Args:
        query: Search query.
        document_ids: Optional document filter.
        limit: Maximum results.

    Returns:
        List of chunk dicts with scores.
    """
    doc_filter = ""
    values: List[Any] = [query]
    if document_ids:
        placeholders = ",".join("?" * len(document_ids))
        doc_filter = f"AND chunks.document_id IN ({placeholders})"
        values.extend(document_ids)

    sql = f"""
        SELECT chunks.*, chunks_fts.rank
        FROM chunks_fts
        JOIN chunks ON chunks.id = chunks_fts.rowid
        WHERE chunks_fts MATCH ?
        {doc_filter}
        ORDER BY chunks_fts.rank
        LIMIT ?
    """
    values.append(limit)

    with get_db() as conn:
        cursor = conn.execute(sql, values)
        return [dict(row) for row in cursor.fetchall()]


# ──────────────────────────────────────────────
# Highlights
# ──────────────────────────────────────────────


def save_highlight(
    document_id: int,
    highlight_type: str,
    text: str,
    page_number: Optional[int] = None,
    section_heading: Optional[str] = None,
    context: Optional[str] = None,
    chunk_id: Optional[int] = None,
) -> int:
    """Save a highlighted passage.

    Args:
        document_id: Document ID.
        highlight_type: Type of highlight.
        text: Highlighted text.
        page_number: Source page.
        section_heading: Section heading.
        context: Surrounding context.
        chunk_id: Associated chunk ID.

    Returns:
        Highlight ID.
    """
    with get_db() as conn:
        cursor = conn.execute(
            """INSERT INTO highlights (document_id, chunk_id, highlight_type,
               text, page_number, section_heading, context)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (document_id, chunk_id, highlight_type, text, page_number, section_heading, context),
        )
        logger.info("Saved highlight for document %d", document_id)
        return cursor.lastrowid


def get_highlights_for_document(document_id: int, highlight_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get highlights for a document.

    Args:
        document_id: Document ID.
        highlight_type: Optional type filter.

    Returns:
        List of highlight dicts.
    """
    query = "SELECT * FROM highlights WHERE document_id = ?"
    values: List[Any] = [document_id]
    if highlight_type:
        query += " AND highlight_type = ?"
        values.append(highlight_type)
    query += " ORDER BY page_number, created_at"

    with get_db() as conn:
        cursor = conn.execute(query, values)
        return [dict(row) for row in cursor.fetchall()]


# ──────────────────────────────────────────────
# Flash Cards
# ──────────────────────────────────────────────


def save_flashcard(
    document_id: int,
    front_text: str,
    back_text: str,
    card_type: str = "question",
    difficulty: str = "medium",
) -> int:
    """Save a flash card.

    Args:
        document_id: Document ID.
        front_text: Question side.
        back_text: Answer side.
        card_type: Card type.
        difficulty: Difficulty level.

    Returns:
        Flash card ID.
    """
    with get_db() as conn:
        cursor = conn.execute(
            """INSERT INTO flashcards (document_id, front_text, back_text,
               card_type, difficulty)
               VALUES (?, ?, ?, ?, ?)""",
            (document_id, front_text, back_text, card_type, difficulty),
        )
        return cursor.lastrowid


def save_flashcards_bulk(document_id: int, cards: List[Dict[str, Any]]) -> None:
    """Save multiple flash cards.

    Args:
        document_id: Document ID.
        cards: List of card dicts.
    """
    with get_db() as conn:
        for card in cards:
            conn.execute(
                """INSERT INTO flashcards (document_id, front_text, back_text,
                   card_type, difficulty)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    document_id,
                    card.get("front", ""),
                    card.get("back", ""),
                    card.get("type", "question"),
                    card.get("difficulty", "medium"),
                ),
            )
        logger.info("Saved %d flashcards for document %d", len(cards), document_id)


def get_flashcards_for_document(document_id: int, learned: Optional[bool] = None) -> List[Dict[str, Any]]:
    """Get flash cards for a document.

    Args:
        document_id: Document ID.
        learned: Optional learned filter.

    Returns:
        List of flash card dicts.
    """
    query = "SELECT * FROM flashcards WHERE document_id = ?"
    values: List[Any] = [document_id]
    if learned is not None:
        query += " AND learned = ?"
        values.append(1 if learned else 0)
    query += " ORDER BY created_at"

    with get_db() as conn:
        cursor = conn.execute(query, values)
        return [dict(row) for row in cursor.fetchall()]


def update_flashcard_status(card_id: int, learned: Optional[bool] = None, for_revision: Optional[bool] = None) -> None:
    """Update flash card status.

    Args:
        card_id: Flash card ID.
        learned: Learned status.
        for_revision: Revision flag.
    """
    fields: List[str] = []
    values: List[Any] = []

    if learned is not None:
        fields.append("learned = ?")
        values.append(1 if learned else 0)
    if for_revision is not None:
        fields.append("for_revision = ?")
        values.append(1 if for_revision else 0)

    if not fields:
        return

    values.append(card_id)
    query = f"UPDATE flashcards SET {', '.join(fields)} WHERE id = ?"

    with get_db() as conn:
        conn.execute(query, values)


# ──────────────────────────────────────────────
# Formula Sheets
# ──────────────────────────────────────────────


def save_formula(
    document_id: int,
    formula: str,
    meaning: Optional[str] = None,
    variables: Optional[str] = None,
    where_used: Optional[str] = None,
    example: Optional[str] = None,
    page_number: Optional[int] = None,
) -> int:
    """Save a formula.

    Args:
        document_id: Document ID.
        formula: Formula text.
        meaning: Formula meaning.
        variables: Variable explanations.
        where_used: Usage context.
        example: Example usage.
        page_number: Source page.

    Returns:
        Formula ID.
    """
    with get_db() as conn:
        cursor = conn.execute(
            """INSERT INTO formula_sheets (document_id, formula, meaning,
               variables, where_used, example, page_number)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (document_id, formula, meaning, variables, where_used, example, page_number),
        )
        return cursor.lastrowid


def save_formulas_bulk(document_id: int, formulas: List[Dict[str, Any]]) -> None:
    """Save multiple formulas.

    Args:
        document_id: Document ID.
        formulas: List of formula dicts.
    """
    with get_db() as conn:
        for formula in formulas:
            conn.execute(
                """INSERT INTO formula_sheets (document_id, formula, meaning,
                   variables, where_used, example, page_number)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    document_id,
                    formula.get("formula", ""),
                    formula.get("meaning"),
                    formula.get("variables"),
                    formula.get("where_used"),
                    formula.get("example"),
                    formula.get("page_number"),
                ),
            )
        logger.info("Saved %d formulas for document %d", len(formulas), document_id)


def get_formulas_for_document(document_id: int) -> List[Dict[str, Any]]:
    """Get formulas for a document.

    Args:
        document_id: Document ID.

    Returns:
        List of formula dicts.
    """
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT * FROM formula_sheets WHERE document_id = ? ORDER BY page_number, created_at",
            (document_id,),
        )
        return [dict(row) for row in cursor.fetchall()]


# ──────────────────────────────────────────────
# Chat History
# ──────────────────────────────────────────────


def save_chat_message(
    document_id: int,
    session_id: str,
    role: str,
    message: str,
    context_chunks: Optional[str] = None,
    source_page: Optional[int] = None,
    source_paragraph: Optional[str] = None,
    confidence: Optional[float] = None,
) -> int:
    """Save a chat message.

    Args:
        document_id: Document ID.
        session_id: Chat session ID.
        role: Message role ('user' or 'assistant').
        message: Message text.
        context_chunks: Context chunks used.
        source_page: Source page number.
        source_paragraph: Source paragraph.
        confidence: Confidence score.

    Returns:
        Message ID.
    """
    with get_db() as conn:
        cursor = conn.execute(
            """INSERT INTO chat_history (document_id, session_id, role, message,
               context_chunks, source_page, source_paragraph, confidence)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (document_id, session_id, role, message, context_chunks, source_page, source_paragraph, confidence),
        )
        return cursor.lastrowid


def get_chat_history(session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Get chat history for a session.

    Args:
        session_id: Chat session ID.
        limit: Maximum messages.

    Returns:
        List of message dicts.
    """
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT * FROM chat_history WHERE session_id = ? ORDER BY created_at ASC LIMIT ?",
            (session_id, limit),
        )
        return [dict(row) for row in cursor.fetchall()]


# ──────────────────────────────────────────────
# Study Notes
# ──────────────────────────────────────────────


def save_study_notes(document_id: int, notes: Dict[str, str]) -> None:
    """Save study notes for a document.

    Args:
        document_id: Document ID.
        notes: Dict of section_name -> content.
    """
    with get_db() as conn:
        for section_name, content in notes.items():
            conn.execute(
                """INSERT INTO study_notes (document_id, section_name, content)
                   VALUES (?, ?, ?)""",
                (document_id, section_name, content),
            )
        logger.info("Saved study notes for document %d", document_id)


def get_study_notes(document_id: int) -> Dict[str, str]:
    """Get study notes for a document.

    Args:
        document_id: Document ID.

    Returns:
        Dict of section_name -> content.
    """
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT section_name, content FROM study_notes WHERE document_id = ?",
            (document_id,),
        )
        return {row["section_name"]: row["content"] for row in cursor.fetchall()}


# ──────────────────────────────────────────────
# Search Cache
# ──────────────────────────────────────────────


def get_search_cache(query_hash: str) -> Optional[Dict[str, Any]]:
    """Get cached search result.

    Args:
        query_hash: Query hash.

    Returns:
        Cached response dict or None.
    """
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT * FROM search_cache WHERE query_hash = ?",
            (query_hash,),
        )
        row = cursor.fetchone()
        if row:
            return {
                "id": row["id"],
                "query_hash": row["query_hash"],
                "query_text": row["query_text"],
                "response": json.loads(row["response"]) if row["response"] else {},
                "document_ids": json.loads(row["document_ids"]) if row["document_ids"] else [],
                "created_at": row["created_at"],
            }
        return None


def save_search_cache(query_hash: str, query_text: str, response: Dict[str, Any], document_ids: List[int]) -> int:
    """Save search result to cache.

    Args:
        query_hash: Query hash.
        query_text: Original query.
        response: Response data.
        document_ids: Related document IDs.

    Returns:
        Cache entry ID.
    """
    with get_db() as conn:
        cursor = conn.execute(
            """INSERT OR REPLACE INTO search_cache (query_hash, query_text, response, document_ids)
               VALUES (?, ?, ?, ?)""",
            (query_hash, query_text, json.dumps(response), json.dumps(document_ids)),
        )
        return cursor.lastrowid


# ──────────────────────────────────────────────
# Stats
# ──────────────────────────────────────────────


def get_dashboard_stats() -> Dict[str, Any]:
    """Get dashboard statistics.

    Returns:
        Dict with dashboard stats.
    """
    counts = dashboard_counts()
    documents = list_documents(status="completed", limit=100)

    subjects = sorted({str(doc.get("subject", "General")) for doc in documents})
    topics = sorted({str(doc.get("topic", "General")) for doc in documents})

    return {
        "total_documents": counts["total"],
        "completed_documents": counts["completed"],
        "subjects": subjects,
        "topics": topics,
    }