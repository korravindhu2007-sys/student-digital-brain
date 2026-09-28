"""File handling utilities for NeuroNote."""

import hashlib
import shutil
import uuid
from pathlib import Path
from typing import Optional, Tuple

from src.config import config
from src.utils.exceptions import (
    FileSizeExceededError,
    UnsupportedFileTypeError,
)
from src.utils.logging import setup_logging

logger = setup_logging(__name__)

# Maximum file sizes in bytes
MAX_SIZES = {
    ".pdf": config.processing.max_pdf_size_mb * 1024 * 1024,
    ".jpg": config.processing.max_image_size_mb * 1024 * 1024,
    ".jpeg": config.processing.max_image_size_mb * 1024 * 1024,
    ".png": config.processing.max_image_size_mb * 1024 * 1024,
    ".tiff": config.processing.max_image_size_mb * 1024 * 1024,
    ".bmp": config.processing.max_image_size_mb * 1024 * 1024,
    ".mp3": config.processing.max_audio_size_mb * 1024 * 1024,
    ".wav": config.processing.max_audio_size_mb * 1024 * 1024,
    ".m4a": config.processing.max_audio_size_mb * 1024 * 1024,
    ".ogg": config.processing.max_audio_size_mb * 1024 * 1024,
    ".txt": config.processing.max_text_size_mb * 1024 * 1024,
    ".md": config.processing.max_text_size_mb * 1024 * 1024,
}


def get_file_extension(filename: str) -> str:
    """Extract and normalize file extension.

    Args:
        filename: Original filename.

    Returns:
        Lowercase file extension with dot.
    """
    return Path(filename).suffix.lower()


def classify_file_type(extension: str) -> Optional[str]:
    """Classify file type from extension.

    Args:
        extension: File extension (e.g., '.pdf').

    Returns:
        File type string: 'pdf', 'image', 'audio', 'text', or None.
    """
    if extension in config.processing.supported_pdf_extensions:
        return "pdf"
    elif extension in config.processing.supported_image_extensions:
        return "image"
    elif extension in config.processing.supported_audio_extensions:
        return "audio"
    elif extension in config.processing.supported_text_extensions:
        return "text"
    return None


def validate_file(file_path: Path) -> Tuple[str, str]:
    """Validate an uploaded file.

    Checks extension, file type, and size limits.

    Args:
        file_path: Path to the uploaded file.

    Returns:
        Tuple of (file_type: str, extension: str).

    Raises:
        UnsupportedFileTypeError: If file extension is not supported.
        FileSizeExceededError: If file exceeds maximum size.
    """
    extension = get_file_extension(file_path.name)
    file_type = classify_file_type(extension)

    if file_type is None:
        raise UnsupportedFileTypeError(file_path.name, extension)

    file_size = file_path.stat().st_size
    max_size = MAX_SIZES.get(extension, 0)

    if max_size > 0 and file_size > max_size:
        raise FileSizeExceededError(file_path.name, file_size, max_size)

    return file_type, extension


def save_upload(file_path: Path, upload_dir: Optional[Path] = None) -> Path:
    """Save a file to the upload directory with a unique name.

    Args:
        file_path: Source file path.
        upload_dir: Target directory (default from config).

    Returns:
        Path to the saved file.
    """
    target_dir = upload_dir or Path(config.upload_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    extension = get_file_extension(file_path.name)
    unique_name = f"{uuid.uuid4().hex}{extension}"
    target_path = target_dir / unique_name

    shutil.copy2(str(file_path), str(target_path))
    logger.info("File saved to %s", target_path)

    return target_path


def compute_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """Compute file hash for integrity verification.

    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm ('sha256' or 'md5').

    Returns:
        Hex digest string.
    """
    hasher = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def ensure_directories() -> None:
    """Create all required application directories."""
    dirs = [
        Path(config.upload_dir),
        Path(config.processed_dir),
        Path(config.models_dir),
        Path(config.database.path).parent,
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    logger.info("Application directories initialized")
