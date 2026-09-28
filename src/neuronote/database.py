from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from .config import get_settings
from .logging_config import get_logger

logger = get_logger(__name__)

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL DEFAULT '',
    file_hash TEXT NOT NULL DEFAULT '',
    pages INTEGER NOT NULL DEFAULT 0,
    uploaded_time TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processed INTEGER NOT NULL DEFAULT 0,
    source_name TEXT NOT NULL DEFAULT '',
    source_type TEXT NOT NULL DEFAULT 'pdf',
    pdf_hash TEXT NOT NULL DEFAULT '',
    title TEXT NOT NULL DEFAULT '',
    file_type TEXT NOT NULL DEFAULT 'pdf',
    file_path TEXT NOT NULL DEFAULT '',
    file_size INTEGER NOT NULL DEFAULT 0,
    page_count INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'pending',
    subject TEXT NOT NULL DEFAULT 'General',
    topic TEXT NOT NULL DEFAULT 'General',
    summary TEXT NOT NULL DEFAULT '',
    raw_text TEXT NOT NULL DEFAULT '',
    structured_json TEXT NOT NULL DEFAULT '{}',
    error_message TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processed_at TEXT
);

CREATE TABLE IF NOT EXISTS chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    page INTEGER NOT NULL DEFAULT 1,
    page_number INTEGER NOT NULL DEFAULT 1,
    chunk_index INTEGER NOT NULL,
    text TEXT NOT NULL,
    subject TEXT NOT NULL DEFAULT 'General',
    chapter TEXT NOT NULL DEFAULT 'General',
    estimated_topic TEXT NOT NULL DEFAULT 'General',
    character_count INTEGER NOT NULL DEFAULT 0,
    word_count INTEGER NOT NULL DEFAULT 0,
    embedding_placeholder TEXT NOT NULL DEFAULT '',
    section_heading TEXT NOT NULL DEFAULT '',
    token_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE,
    UNIQUE(document_id, chunk_index)
);

CREATE TABLE IF NOT EXISTS study_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    title TEXT NOT NULL DEFAULT '',
    section_name TEXT NOT NULL DEFAULT '',
    content TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'General',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS flashcards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    question TEXT NOT NULL DEFAULT '',
    answer TEXT NOT NULL DEFAULT '',
    front_text TEXT NOT NULL DEFAULT '',
    back_text TEXT NOT NULL DEFAULT '',
    difficulty TEXT NOT NULL DEFAULT 'medium',
    card_type TEXT NOT NULL DEFAULT 'question',
    learned INTEGER NOT NULL DEFAULT 0,
    for_revision INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS formula_sheet (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    formula TEXT NOT NULL,
    meaning TEXT NOT NULL DEFAULT '',
    example TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS formula_sheets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    formula TEXT NOT NULL,
    meaning TEXT NOT NULL DEFAULT '',
    variables TEXT NOT NULL DEFAULT '',
    where_used TEXT NOT NULL DEFAULT '',
    example TEXT NOT NULL DEFAULT '',
    page_number INTEGER,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS highlights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    page INTEGER NOT NULL DEFAULT 1,
    page_number INTEGER NOT NULL DEFAULT 1,
    text TEXT NOT NULL,
    reason TEXT NOT NULL DEFAULT '',
    highlight_type TEXT NOT NULL DEFAULT 'important',
    section_heading TEXT NOT NULL DEFAULT '',
    context TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS chat_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER,
    question TEXT NOT NULL DEFAULT '',
    answer TEXT NOT NULL DEFAULT '',
    session_id TEXT NOT NULL DEFAULT '',
    role TEXT NOT NULL DEFAULT '',
    message TEXT NOT NULL DEFAULT '',
    timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_hash TEXT NOT NULL UNIQUE,
    response TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS search_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query_hash TEXT NOT NULL UNIQUE,
    query_json TEXT NOT NULL DEFAULT '{}',
    query_text TEXT NOT NULL DEFAULT '',
    response_json TEXT NOT NULL DEFAULT '{}',
    response TEXT NOT NULL DEFAULT '{}',
    document_ids TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS concepts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    concept TEXT NOT NULL,
    definition TEXT NOT NULL DEFAULT '',
    subject TEXT NOT NULL DEFAULT 'General',
    topic TEXT NOT NULL DEFAULT 'General',
    importance TEXT NOT NULL DEFAULT 'medium',
    related_concepts TEXT NOT NULL DEFAULT '[]',
    FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS quizzes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER,
    subject TEXT NOT NULL DEFAULT 'General',
    topic TEXT NOT NULL DEFAULT 'General',
    questions_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS revisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER,
    subject TEXT NOT NULL DEFAULT 'General',
    topic TEXT NOT NULL DEFAULT 'General',
    plan_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_documents_file_hash ON documents(file_hash);
CREATE INDEX IF NOT EXISTS idx_documents_pdf_hash ON documents(pdf_hash);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
CREATE INDEX IF NOT EXISTS idx_chunks_document ON chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_chunks_text ON chunks(text);
CREATE INDEX IF NOT EXISTS idx_cache_request_hash ON cache(request_hash);
CREATE INDEX IF NOT EXISTS idx_search_cache_hash ON search_cache(query_hash);
"""

DOCUMENT_COLUMNS = {
    "filename": "TEXT NOT NULL DEFAULT ''",
    "file_hash": "TEXT NOT NULL DEFAULT ''",
    "pages": "INTEGER NOT NULL DEFAULT 0",
    "uploaded_time": "TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP",
    "processed": "INTEGER NOT NULL DEFAULT 0",
    "source_name": "TEXT NOT NULL DEFAULT ''",
    "source_type": "TEXT NOT NULL DEFAULT 'pdf'",
    "pdf_hash": "TEXT NOT NULL DEFAULT ''",
    "title": "TEXT NOT NULL DEFAULT ''",
    "file_type": "TEXT NOT NULL DEFAULT 'pdf'",
    "file_path": "TEXT NOT NULL DEFAULT ''",
    "file_size": "INTEGER NOT NULL DEFAULT 0",
    "page_count": "INTEGER NOT NULL DEFAULT 0",
    "status": "TEXT NOT NULL DEFAULT 'pending'",
    "subject": "TEXT NOT NULL DEFAULT 'General'",
    "topic": "TEXT NOT NULL DEFAULT 'General'",
    "summary": "TEXT NOT NULL DEFAULT ''",
    "raw_text": "TEXT NOT NULL DEFAULT ''",
    "structured_json": "TEXT NOT NULL DEFAULT '{}'",
    "error_message": "TEXT",
    "created_at": "TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP",
    "processed_at": "TEXT",
}


class DatabaseManager:
    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or get_settings().database_path

    def connect(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(SCHEMA)
        self._migrate(conn)
        return conn

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        conn = self.connect()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def initialize_database(self) -> None:
        with self.connection() as conn:
            conn.commit()

    def insert_document(
        self,
        filename: str,
        file_hash: str,
        pages: int,
        *,
        file_path: str = "",
        file_size: int = 0,
        subject: str = "General",
        topic: str = "General",
        raw_text: str = "",
        processed: bool = False,
        summary: str = "",
        structured_json: dict[str, Any] | None = None,
    ) -> int:
        payload = structured_json or {}
        with self.connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO documents (
                    filename, file_hash, pages, processed, source_name, source_type, pdf_hash,
                    title, file_type, file_path, file_size, page_count, status, subject, topic,
                    summary, raw_text, structured_json, processed_at
                )
                VALUES (?, ?, ?, ?, ?, 'pdf', ?, ?, 'pdf', ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (
                    filename,
                    file_hash,
                    pages,
                    1 if processed else 0,
                    filename,
                    file_hash,
                    filename,
                    file_path,
                    file_size,
                    pages,
                    "completed" if processed else "pending",
                    subject,
                    topic,
                    summary,
                    raw_text,
                    json.dumps(payload, ensure_ascii=False),
                ),
            )
            return int(cursor.lastrowid or 0)

    def insert_chunk(
        self,
        document_id: int,
        page: int,
        chunk_index: int,
        text: str,
        embedding_placeholder: str = "",
        subject: str = "General",
        chapter: str = "General",
        estimated_topic: str = "General",
    ) -> int:
        word_count = len(text.split())
        with self.connection() as conn:
            cursor = conn.execute(
                """
                INSERT OR REPLACE INTO chunks (
                    document_id, page, page_number, chunk_index, text, subject, chapter, estimated_topic,
                    character_count, word_count, embedding_placeholder, token_count
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    document_id,
                    page,
                    page,
                    chunk_index,
                    text,
                    subject,
                    chapter,
                    estimated_topic,
                    len(text),
                    word_count,
                    embedding_placeholder,
                    word_count,
                ),
            )
            return int(cursor.lastrowid or 0)

    def insert_flashcard(
        self,
        document_id: int,
        question: str,
        answer: str,
        difficulty: str = "medium",
    ) -> int:
        with self.connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO flashcards (document_id, question, answer, front_text, back_text, difficulty)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (document_id, question, answer, question, answer, difficulty),
            )
            return int(cursor.lastrowid or 0)

    def insert_formula(self, document_id: int, formula: str, meaning: str = "", example: str = "") -> int:
        with self.connection() as conn:
            cursor = conn.execute(
                "INSERT INTO formula_sheet (document_id, formula, meaning, example) VALUES (?, ?, ?, ?)",
                (document_id, formula, meaning, example),
            )
            return int(cursor.lastrowid or 0)

    def insert_highlight(self, document_id: int, page: int, text: str, reason: str = "") -> int:
        with self.connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO highlights (document_id, page, page_number, text, reason)
                VALUES (?, ?, ?, ?, ?)
                """,
                (document_id, page, page, text, reason),
            )
            return int(cursor.lastrowid or 0)

    def save_chat(self, question: str, answer: str, document_id: int | None = None) -> int:
        with self.connection() as conn:
            cursor = conn.execute(
                "INSERT INTO chat_history (document_id, question, answer) VALUES (?, ?, ?)",
                (document_id, question, answer),
            )
            return int(cursor.lastrowid or 0)

    def load_chat(self, limit: int = 50) -> list[dict[str, Any]]:
        with self.connection() as conn:
            rows = conn.execute(
                "SELECT * FROM chat_history ORDER BY timestamp DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(row) for row in rows]

    def cache_lookup(self, request_hash: str) -> str | None:
        with self.connection() as conn:
            row = conn.execute("SELECT response FROM cache WHERE request_hash = ?", (request_hash,)).fetchone()
            return str(row["response"]) if row else None

    def cache_store(self, request_hash: str, response: str) -> int:
        with self.connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO cache (request_hash, response)
                VALUES (?, ?)
                ON CONFLICT(request_hash) DO UPDATE SET response = excluded.response
                """,
                (request_hash, response),
            )
            return int(cursor.lastrowid or 0)

    def get_document_by_hash(self, file_hash: str) -> dict[str, Any] | None:
        with self.connection() as conn:
            row = conn.execute(
                """
                SELECT * FROM documents
                WHERE file_hash = ? OR pdf_hash = ?
                ORDER BY uploaded_time DESC, created_at DESC
                LIMIT 1
                """,
                (file_hash, file_hash),
            ).fetchone()
            return dict(row) if row else None

    def get_document(self, document_id: int) -> dict[str, Any] | None:
        with self.connection() as conn:
            row = conn.execute("SELECT * FROM documents WHERE id = ?", (document_id,)).fetchone()
            return dict(row) if row else None

    def list_documents(self) -> list[dict[str, Any]]:
        with self.connection() as conn:
            rows = conn.execute("SELECT * FROM documents ORDER BY uploaded_time DESC, created_at DESC").fetchall()
            return [dict(row) for row in rows]

    def get_chunks(self, document_id: int | None = None) -> list[dict[str, Any]]:
        sql = "SELECT * FROM chunks"
        params: tuple[Any, ...] = ()
        if document_id is not None:
            sql += " WHERE document_id = ?"
            params = (document_id,)
        sql += " ORDER BY document_id DESC, chunk_index"
        with self.connection() as conn:
            rows = conn.execute(sql, params).fetchall()
            return [dict(row) for row in rows]

    def search_chunks(self, query: str, document_ids: list[int] | None = None, limit: int = 10) -> list[dict[str, Any]]:
        terms = [term.lower() for term in query.split() if term.strip()]
        if not terms:
            return []
        chunks = self.get_chunks()
        if document_ids:
            wanted = set(document_ids)
            chunks = [chunk for chunk in chunks if int(chunk["document_id"]) in wanted]
        ranked = []
        for chunk in chunks:
            text = str(chunk.get("text", ""))
            lower = text.lower()
            score = sum(lower.count(term) for term in terms)
            if score:
                ranked.append((score, chunk))
        ranked.sort(key=lambda item: item[0], reverse=True)
        return [chunk for _, chunk in ranked[:limit]]

    def _migrate(self, conn: sqlite3.Connection) -> None:
        self._ensure_columns(conn, "documents", DOCUMENT_COLUMNS)
        self._ensure_columns(
            conn,
            "chunks",
            {
                "page": "INTEGER NOT NULL DEFAULT 1",
                "page_number": "INTEGER NOT NULL DEFAULT 1",
                "subject": "TEXT NOT NULL DEFAULT 'General'",
                "chapter": "TEXT NOT NULL DEFAULT 'General'",
                "estimated_topic": "TEXT NOT NULL DEFAULT 'General'",
                "character_count": "INTEGER NOT NULL DEFAULT 0",
                "word_count": "INTEGER NOT NULL DEFAULT 0",
                "embedding_placeholder": "TEXT NOT NULL DEFAULT ''",
                "section_heading": "TEXT NOT NULL DEFAULT ''",
                "token_count": "INTEGER NOT NULL DEFAULT 0",
            },
        )
        self._ensure_columns(
            conn,
            "search_cache",
            {
                "query_json": "TEXT NOT NULL DEFAULT '{}'",
                "query_text": "TEXT NOT NULL DEFAULT ''",
                "response_json": "TEXT NOT NULL DEFAULT '{}'",
                "response": "TEXT NOT NULL DEFAULT '{}'",
                "document_ids": "TEXT NOT NULL DEFAULT '[]'",
            },
        )

    @staticmethod
    def _ensure_columns(conn: sqlite3.Connection, table: str, columns: dict[str, str]) -> None:
        existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
        for name, ddl in columns.items():
            if name not in existing:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}")


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    return DatabaseManager(db_path).connect()


def initialize_database(db_path: Path | None = None) -> None:
    DatabaseManager(db_path).initialize_database()


def reset_database(db_path: Path) -> None:
    if db_path.exists():
        db_path.unlink()
    initialize_database(db_path)


def save_document_record(structured: dict[str, Any], db_path: Path | None = None) -> int:
    manager = DatabaseManager(db_path)
    document_id = manager.insert_document(
        filename=str(structured.get("source_name", "unknown")),
        file_hash=str(structured.get("pdf_hash", "")),
        pages=int(structured.get("page_count") or len(structured.get("pages", [])) or 0),
        subject=str(structured.get("subject", "General")),
        topic=str(structured.get("topic", "General")),
        raw_text=str(structured.get("raw_text", "")),
        processed=True,
        summary=str(structured.get("summary", "")),
        structured_json=structured,
    )
    with manager.connection() as conn:
        for concept in structured.get("concepts", []):
            if not isinstance(concept, dict):
                continue
            conn.execute(
                """
                INSERT INTO concepts (document_id, concept, definition, subject, topic, importance, related_concepts)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    document_id,
                    concept.get("concept", ""),
                    concept.get("definition", ""),
                    concept.get("subject", structured.get("subject", "General")),
                    concept.get("topic", structured.get("topic", "General")),
                    concept.get("importance", "medium"),
                    json.dumps(concept.get("related_concepts", []), ensure_ascii=False),
                ),
            )
    return document_id


def save_pdf_document_record(structured: dict[str, Any], pdf_hash: str, db_path: Path | None = None) -> int:
    payload = dict(structured)
    payload["pdf_hash"] = pdf_hash
    return save_document_record(payload, db_path=db_path)


def get_document_by_hash(pdf_hash: str, db_path: Path | None = None) -> dict[str, Any] | None:
    return DatabaseManager(db_path).get_document_by_hash(pdf_hash)


def get_document(document_id: int, db_path: Path | None = None) -> dict[str, Any] | None:
    return DatabaseManager(db_path).get_document(document_id)


def latest_pdf_document(db_path: Path | None = None) -> dict[str, Any] | None:
    documents = [doc for doc in DatabaseManager(db_path).list_documents() if doc.get("source_type") == "pdf"]
    return documents[0] if documents else None


def find_pdf_document(
    subject: str | None = None,
    topic: str | None = None,
    db_path: Path | None = None,
) -> dict[str, Any] | None:
    subject_value = (subject or "").lower()
    topic_value = (topic or "").lower()
    for document in DatabaseManager(db_path).list_documents():
        if subject_value and subject_value not in str(document.get("subject", "")).lower():
            continue
        if topic_value and topic_value not in str(document.get("topic", "")).lower():
            continue
        return document
    return None


def list_documents(db_path: Path | None = None) -> list[dict[str, Any]]:
    return DatabaseManager(db_path).list_documents()


def list_concepts(db_path: Path | None = None) -> list[dict[str, Any]]:
    with DatabaseManager(db_path).connection() as conn:
        return [dict(row) for row in conn.execute("SELECT * FROM concepts ORDER BY concept").fetchall()]


def search_concepts(field: str, value: str, db_path: Path | None = None) -> list[dict[str, Any]]:
    allowed = {"subject", "topic", "concept", "definition"}
    if field not in allowed:
        raise ValueError(f"Unsupported search field: {field}")
    with DatabaseManager(db_path).connection() as conn:
        rows = conn.execute(
            f"SELECT * FROM concepts WHERE LOWER({field}) LIKE LOWER(?) ORDER BY concept",
            (f"%{value}%",),
        ).fetchall()
        return [dict(row) for row in rows]


def keyword_search(keyword: str, db_path: Path | None = None) -> list[dict[str, Any]]:
    hits = DatabaseManager(db_path).search_chunks(keyword, limit=20)
    if hits:
        return hits
    with DatabaseManager(db_path).connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM documents
            WHERE LOWER(raw_text) LIKE LOWER(?)
            ORDER BY uploaded_time DESC, created_at DESC
            """,
            (f"%{keyword}%",),
        ).fetchall()
        return [dict(row) for row in rows]


def search_documents(
    subject: str | None = None,
    topic: str | None = None,
    keyword: str | None = None,
    db_path: Path | None = None,
) -> list[dict[str, Any]]:
    documents = DatabaseManager(db_path).list_documents()
    results = []
    for document in documents:
        if subject and subject.lower() not in str(document.get("subject", "")).lower():
            continue
        if topic and topic.lower() not in str(document.get("topic", "")).lower():
            continue
        if keyword and keyword.lower() not in str(document.get("raw_text", "")).lower():
            continue
        results.append(document)
    return results


def save_quiz_record(
    subject: str,
    topic: str,
    questions: list[dict[str, Any]],
    db_path: Path | None = None,
    document_id: int | None = None,
) -> int:
    with DatabaseManager(db_path).connection() as conn:
        cursor = conn.execute(
            "INSERT INTO quizzes (document_id, subject, topic, questions_json) VALUES (?, ?, ?, ?)",
            (document_id, subject, topic, json.dumps(questions, ensure_ascii=False)),
        )
        return int(cursor.lastrowid or 0)


def latest_quiz_record(document_id: int | None = None, db_path: Path | None = None) -> dict[str, Any] | None:
    query = "SELECT * FROM quizzes"
    params: tuple[Any, ...] = ()
    if document_id is not None:
        query += " WHERE document_id = ?"
        params = (document_id,)
    query += " ORDER BY created_at DESC LIMIT 1"
    with DatabaseManager(db_path).connection() as conn:
        row = conn.execute(query, params).fetchone()
        return dict(row) if row else None


def save_revision_record(
    subject: str,
    topic: str,
    plan: dict[str, Any] | list[dict[str, Any]],
    db_path: Path | None = None,
    document_id: int | None = None,
) -> int:
    with DatabaseManager(db_path).connection() as conn:
        cursor = conn.execute(
            "INSERT INTO revisions (document_id, subject, topic, plan_json) VALUES (?, ?, ?, ?)",
            (document_id, subject, topic, json.dumps(plan, ensure_ascii=False)),
        )
        return int(cursor.lastrowid or 0)


def latest_revision_record(document_id: int | None = None, db_path: Path | None = None) -> dict[str, Any] | None:
    query = "SELECT * FROM revisions"
    params: tuple[Any, ...] = ()
    if document_id is not None:
        query += " WHERE document_id = ?"
        params = (document_id,)
    query += " ORDER BY created_at DESC LIMIT 1"
    with DatabaseManager(db_path).connection() as conn:
        row = conn.execute(query, params).fetchone()
        return dict(row) if row else None


def get_search_cache(query_hash: str, db_path: Path | None = None) -> dict[str, Any] | None:
    with DatabaseManager(db_path).connection() as conn:
        row = conn.execute("SELECT response_json FROM search_cache WHERE query_hash = ?", (query_hash,)).fetchone()
        if not row:
            return None
        loaded = json.loads(str(row["response_json"]))
        return loaded if isinstance(loaded, dict) else None


def save_search_cache(
    query_hash: str,
    query: dict[str, Any],
    response: dict[str, Any],
    db_path: Path | None = None,
) -> int:
    with DatabaseManager(db_path).connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO search_cache (query_hash, query_json, query_text, response_json, response, document_ids)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(query_hash) DO UPDATE SET response_json = excluded.response_json, response = excluded.response
            """,
            (
                query_hash,
                json.dumps(query, ensure_ascii=False),
                str(query),
                json.dumps(response, ensure_ascii=False),
                json.dumps(response, ensure_ascii=False),
                json.dumps(query.get("document_ids", []), ensure_ascii=False),
            ),
        )
        return int(cursor.lastrowid or 0)


def dashboard_counts(db_path: Path | None = None) -> dict[str, int]:
    documents = DatabaseManager(db_path).list_documents()
    with DatabaseManager(db_path).connection() as conn:
        quiz_count = int(conn.execute("SELECT COUNT(*) FROM quizzes").fetchone()[0])
        revision_count = int(conn.execute("SELECT COUNT(*) FROM revisions").fetchone()[0])
    return {
        "documents": len(documents),
        "subjects": len({str(doc.get("subject", "General")) for doc in documents}),
        "topics": len({str(doc.get("topic", "General")) for doc in documents}),
        "quizzes": quiz_count,
        "revisions": revision_count,
    }
