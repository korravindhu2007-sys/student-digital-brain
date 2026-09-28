"""SQLite connection management for NeuroNote."""

import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from src.config import config
from src.utils.logging import setup_logging

logger = setup_logging(__name__)

_local = threading.local()


def get_connection() -> sqlite3.Connection:
    """Get a thread-local SQLite connection.

    Creates a new connection if one does not exist for the current thread.
    Enables WAL mode, foreign keys, and sets busy timeout.

    Returns:
        SQLite Connection object.
    """
    if not hasattr(_local, "connection") or _local.connection is None:
        db_path = Path(config.database.path)
        db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        conn.execute(f"PRAGMA busy_timeout={config.database.busy_timeout};")
        conn.execute(f"PRAGMA cache_size={config.database.cache_size};")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA temp_store=MEMORY;")

        _local.connection = conn
        logger.debug("Database connection established: %s", db_path)

    return _local.connection


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """Context manager for database access.

    Provides a connection and ensures proper cleanup.

    Yields:
        SQLite Connection object.
    """
    conn = get_connection()
    try:
        yield conn
    except sqlite3.Error as e:
        conn.rollback()
        logger.error("Database error: %s", e)
        raise
    finally:
        conn.commit()


def close_connection() -> None:
    """Close the thread-local database connection if open."""
    if hasattr(_local, "connection") and _local.connection:
        _local.connection.close()
        _local.connection = None
        logger.debug("Database connection closed")
