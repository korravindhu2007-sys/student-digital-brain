"""Custom exceptions for NeuroNote."""

from typing import Any, Optional


class NeuroNoteError(Exception):
    """Base exception for all NeuroNote errors."""

    def __init__(self, message: str, details: Optional[Any] = None) -> None:
        self.message = message
        self.details = details
        super().__init__(self.message)


class FileValidationError(NeuroNoteError):
    """Raised when a file fails validation checks."""

    def __init__(
        self,
        message: str,
        filename: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> None:
        self.filename = filename
        self.reason = reason
        super().__init__(message, details={"filename": filename, "reason": reason})


class FileSizeExceededError(FileValidationError):
    """Raised when a file exceeds the maximum allowed size."""

    def __init__(
        self,
        filename: str,
        size_bytes: int,
        max_size_bytes: int,
    ) -> None:
        self.size_bytes = size_bytes
        self.max_size_bytes = max_size_bytes
        super().__init__(
            message=(
                f"File '{filename}' size ({size_bytes / 1024 / 1024:.1f} MB) "
                f"exceeds maximum ({max_size_bytes / 1024 / 1024:.1f} MB)"
            ),
            filename=filename,
            reason="size_exceeded",
        )


class UnsupportedFileTypeError(FileValidationError):
    """Raised when a file type is not supported."""

    def __init__(self, filename: str, extension: str) -> None:
        self.extension = extension
        super().__init__(
            message=f"Unsupported file type '{extension}' for file '{filename}'",
            filename=filename,
            reason="unsupported_type",
        )


class ProcessingError(NeuroNoteError):
    """Raised when document processing fails."""

    def __init__(
        self,
        message: str,
        module: Optional[str] = None,
        document_id: Optional[int] = None,
    ) -> None:
        self.module = module
        self.document_id = document_id
        super().__init__(
            message,
            details={"module": module, "document_id": document_id},
        )


class PDFExtractionError(ProcessingError):
    """Raised when PDF text extraction fails."""

    def __init__(
        self,
        message: str,
        document_id: Optional[int] = None,
        page: Optional[int] = None,
    ) -> None:
        self.page = page
        super().__init__(
            message=message,
            module="pdf_extractor",
            document_id=document_id,
        )


class OCRError(ProcessingError):
    """Raised when OCR processing fails."""

    def __init__(
        self,
        message: str,
        document_id: Optional[int] = None,
        image_path: Optional[str] = None,
    ) -> None:
        self.image_path = image_path
        super().__init__(
            message=message,
            module="ocr",
            document_id=document_id,
        )


class STTError(ProcessingError):
    """Raised when speech-to-text processing fails."""

    def __init__(
        self,
        message: str,
        document_id: Optional[int] = None,
        audio_path: Optional[str] = None,
    ) -> None:
        self.audio_path = audio_path
        super().__init__(
            message=message,
            module="stt",
            document_id=document_id,
        )


class LLMError(NeuroNoteError):
    """Raised when LLM inference fails."""

    def __init__(
        self,
        message: str,
        chunk_id: Optional[int] = None,
        retry_count: Optional[int] = None,
    ) -> None:
        self.chunk_id = chunk_id
        self.retry_count = retry_count
        super().__init__(
            message,
            details={"chunk_id": chunk_id, "retry_count": retry_count},
        )


class JSONParseError(LLMError):
    """Raised when LLM output cannot be parsed as valid JSON."""

    def __init__(
        self,
        raw_output: str,
        parse_error: str,
        chunk_id: Optional[int] = None,
    ) -> None:
        self.raw_output = raw_output[:500]  # Truncate for logging
        self.parse_error = parse_error
        super().__init__(
            message=f"Failed to parse LLM output as JSON: {parse_error}",
            chunk_id=chunk_id,
        )


class DatabaseError(NeuroNoteError):
    """Raised when a database operation fails."""

    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
    ) -> None:
        self.operation = operation
        super().__init__(
            message,
            details={"operation": operation},
        )


class ModelNotFoundError(NeuroNoteError):
    """Raised when a required model file is not found."""

    def __init__(self, model_path: str, model_name: str) -> None:
        self.model_path = model_path
        self.model_name = model_name
        super().__init__(
            message=(
                f"Model '{model_name}' not found at '{model_path}'. "
                f"Please download the model and place it at the expected path."
            ),
            details={"model_path": model_path, "model_name": model_name},
        )
