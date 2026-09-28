"""SQLite database schema and initialization for NeuroNote."""

from typing import List

from src.database.connection import get_db
from src.utils.logging import setup_logging

logger = setup_logging(__name__)

# Full DDL for all tables
SCHEMA_SQL = """
-- 1. Subjects table
CREATE TABLE IF NOT EXISTS subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    color TEXT DEFAULT '#4A90D9',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Documents table
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    file_type TEXT NOT NULL CHECK(file_type IN ('pdf')),
    file_path TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    page_count INTEGER DEFAULT 0,
    raw_text TEXT,
    structured_json TEXT,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK(status IN ('pending', 'processing', 'completed', 'failed')),
    subject TEXT DEFAULT 'General',
    topic TEXT DEFAULT 'General',
    pdf_hash TEXT UNIQUE,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP
);

-- 3. Chunks table (semantic chunks from PDFs)
CREATE TABLE IF NOT EXISTS chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    chunk_index INTEGER NOT NULL,
    text TEXT NOT NULL,
    page_number INTEGER,
    section_heading TEXT,
    token_count INTEGER DEFAULT 0,
    embedding BLOB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    UNIQUE(document_id, chunk_index)
);

-- 4. Highlights table
CREATE TABLE IF NOT EXISTS highlights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    chunk_id INTEGER,
    highlight_type TEXT NOT NULL
        CHECK(highlight_type IN ('definition', 'formula', 'important', 'algorithm', 'theorem')),
    text TEXT NOT NULL,
    page_number INTEGER,
    section_heading TEXT,
    context TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    FOREIGN KEY (chunk_id) REFERENCES chunks(id) ON DELETE SET NULL
);

-- 5. Flash cards table
CREATE TABLE IF NOT EXISTS flashcards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    front_text TEXT NOT NULL,
    back_text TEXT NOT NULL,
    card_type TEXT DEFAULT 'question'
        CHECK(card_type IN ('question', 'definition', 'formula')),
    difficulty TEXT DEFAULT 'medium'
        CHECK(difficulty IN ('easy', 'medium', 'hard')),
    learned BOOLEAN DEFAULT 0,
    for_revision BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);

-- 6. Formula sheets table
CREATE TABLE IF NOT EXISTS formula_sheets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    formula TEXT NOT NULL,
    meaning TEXT,
    variables TEXT,
    where_used TEXT,
    example TEXT,
    page_number INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);

-- 7. Chat history table
CREATE TABLE IF NOT EXISTS chat_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
    message TEXT NOT NULL,
    context_chunks TEXT,
    source_page INTEGER,
    source_paragraph TEXT,
    confidence REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);

-- 8. Study notes table
CREATE TABLE IF NOT EXISTS study_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    section_name TEXT NOT NULL,
    content TEXT NOT NULL,
    expanded BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);

-- 9. Search cache table
CREATE TABLE IF NOT EXISTS search_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query_hash TEXT NOT NULL UNIQUE,
    query_text TEXT NOT NULL,
    response TEXT NOT NULL,
    document_ids TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# Indexes for performance
INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);",
    "CREATE INDEX IF NOT EXISTS idx_documents_subject ON documents(subject);",
    "CREATE INDEX IF NOT EXISTS idx_documents_topic ON documents(topic);",
    "CREATE INDEX IF NOT EXISTS idx_documents_hash ON documents(pdf_hash);",
    "CREATE INDEX IF NOT EXISTS idx_chunks_document ON chunks(document_id);",
    "CREATE INDEX IF NOT EXISTS idx_chunks_page ON chunks(page_number);",
    "CREATE INDEX IF NOT EXISTS idx_highlights_document ON highlights(document_id);",
    "CREATE INDEX IF NOT EXISTS idx_highlights_type ON highlights(highlight_type);",
    "CREATE INDEX IF NOT EXISTS idx_flashcards_document ON flashcards(document_id);",
    "CREATE INDEX IF NOT EXISTS idx_formulas_document ON formula_sheets(document_id);",
    "CREATE INDEX IF NOT EXISTS idx_chat_session ON chat_history(session_id);",
    "CREATE INDEX IF NOT EXISTS idx_chat_document ON chat_history(document_id);",
    "CREATE INDEX IF NOT EXISTS idx_study_notes_document ON study_notes(document_id);",
    "CREATE INDEX IF NOT EXISTS idx_search_cache_hash ON search_cache(query_hash);",
]

# FTS5 full-text search virtual table
FTS5_SQL = """
CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
    text,
    section_heading,
    content='chunks',
    content_rowid='id',
    tokenize='porter unicode61'
);

CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON chunks BEGIN
    INSERT INTO chunks_fts(rowid, text, section_heading)
    VALUES (new.id, new.text, new.section_heading);
END;

CREATE TRIGGER IF NOT EXISTS chunks_ad AFTER DELETE ON chunks BEGIN
    INSERT INTO chunks_fts(chunks_fts, rowid, text, section_heading)
    VALUES ('delete', old.id, old.text, old.section_heading);
END;

CREATE TRIGGER IF NOT EXISTS chunks_au AFTER UPDATE ON chunks BEGIN
    INSERT INTO chunks_fts(chunks_fts, rowid, text, section_heading)
    VALUES ('delete', old.id, old.text, old.section_heading);
    INSERT INTO chunks_fts(rowid, text, section_heading)
    VALUES (new.id, new.text, new.section_heading);
END;
"""


def initialize_database() -> None:
    """Create all tables, indexes, and FTS5 virtual table.

    Safe to call multiple times; uses IF NOT EXISTS.
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Create tables
        cursor.executescript(SCHEMA_SQL)
        logger.info("Database tables created successfully")

        # Create indexes
        for index_sql in INDEXES_SQL:
            cursor.execute(index_sql)
        logger.info("Database indexes created successfully")

        # Create FTS5 virtual table and triggers
        cursor.executescript(FTS5_SQL)
        logger.info("FTS5 full-text search initialized")

        conn.commit()

    logger.info("Database initialization complete")


def get_table_names() -> List[str]:
    """Get list of all table names in the database.

    Returns:
        List of table names.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        return [row["name"] for row in cursor.fetchall()]