"""Database initialization module.

Run this script to initialize the NeuroNote database.
"""

from src.database.schema import initialize_database
from src.utils.logging import setup_logging

logger = setup_logging(__name__)


def main():
    """Initialize the database."""
    print("Initializing NeuroNote database...")
    try:
        initialize_database()
        print("✓ Database initialized successfully")
        print("  - Tables created")
        print("  - Indexes created")
        print("  - FTS5 full-text search enabled")
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        return 1
    return 0


if __name__ == "__main__":
    exit(main())