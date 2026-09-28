"""Logging configuration for NeuroNote."""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional

from src.config import config


def setup_logging(
    name: str = "neuronote",
    level: Optional[str] = None,
    log_file: Optional[str] = None,
) -> logging.Logger:
    """Configure and return a logger instance.

    Sets up both console and file handlers with a consistent format.
    Creates the log directory if it does not exist.

    Args:
        name: Logger name (typically __name__ from caller).
        level: Override log level (default from config).
        log_file: Override log file path (default from config).

    Returns:
        Configured Logger instance.
    """
    logger = logging.getLogger(name)
    log_level = (level or config.logging.level).upper()
    logger.setLevel(getattr(logging, log_level, logging.INFO))

    if logger.handlers:
        return logger  # Avoid duplicate handlers

    formatter = logging.Formatter(
        fmt=config.logging.format,
        datefmt=config.logging.date_format,
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler
    file_path = log_file or config.logging.file_path
    if file_path:
        log_dir = Path(file_path).parent
        log_dir.mkdir(parents=True, exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            filename=file_path,
            maxBytes=config.logging.max_file_size_mb * 1024 * 1024,
            backupCount=config.logging.backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
