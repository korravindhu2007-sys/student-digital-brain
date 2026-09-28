"""Configuration management for NeuroNote.

Loads settings from environment variables with sensible defaults
for a local, offline application.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class DatabaseConfig:
    """SQLite database configuration."""

    path: str = field(
        default_factory=lambda: os.getenv(
            "NEURONOTE_DB_PATH",
            str(Path.cwd() / "database" / "neuronote.db"),
        )
    )
    wal_mode: bool = True
    busy_timeout: int = 5000
    cache_size: int = -20000  # 20 MB


@dataclass
class ProcessingConfig:
    """Document processing configuration."""

    max_pdf_size_mb: int = 100
    max_image_size_mb: int = 50
    max_audio_size_mb: int = 500
    max_text_size_mb: int = 10
    supported_pdf_extensions: List[str] = field(default_factory=lambda: [".pdf"])
    supported_image_extensions: List[str] = field(
        default_factory=lambda: [".jpg", ".jpeg", ".png", ".tiff", ".bmp"]
    )
    supported_audio_extensions: List[str] = field(
        default_factory=lambda: [".mp3", ".wav", ".m4a", ".ogg"]
    )
    supported_text_extensions: List[str] = field(default_factory=lambda: [".txt", ".md"])


@dataclass
class OCRConfig:
    """Tesseract OCR configuration."""

    tesseract_cmd: str = field(default_factory=lambda: os.getenv("TESSERACT_CMD", "tesseract"))
    language: str = "eng"
    dpi: int = 300
    oem_mode: int = 1  # LSTM neural network engine
    psm_mode: int = 6  # Assume uniform block of text
    preprocessing_enabled: bool = True


@dataclass
class STTConfig:
    """Speech-to-text (Whisper.cpp) configuration."""

    model_path: str = field(
        default_factory=lambda: os.getenv(
            "WHISPER_MODEL_PATH",
            str(Path.cwd() / "models" / "ggml-small-q5_0.bin"),
        )
    )
    model_name: str = "ggml-small-q5_0"
    language: str = "auto"
    num_threads: int = field(default_factory=lambda: int(os.getenv("WHISPER_THREADS", "4")))
    chunk_seconds: int = 30
    sample_rate: int = 16000


@dataclass
class LLMConfig:
    """Large language model (llama.cpp) configuration."""

    model_path: str = field(
        default_factory=lambda: os.getenv(
            "LLM_MODEL_PATH",
            str(Path.cwd() / "models" / "Phi-3-mini-4k-instruct-q4_k_m.gguf"),
        )
    )
    n_ctx: int = 4096
    n_threads: int = field(default_factory=lambda: int(os.getenv("LLM_THREADS", "4")))
    n_batch: int = 512
    temperature: float = 0.3
    top_p: float = 0.9
    top_k: int = 40
    repeat_penalty: float = 1.1
    max_tokens: int = 2048


@dataclass
class ChunkingConfig:
    """Text chunking configuration for LLM processing."""

    chunk_size_tokens: int = 2048
    chunk_overlap_tokens: int = 256
    context_window: int = 4096


@dataclass
class KnowledgeGraphConfig:
    """Knowledge graph configuration."""

    similarity_threshold: float = 0.3
    max_nodes_per_subject: int = 5000
    relationship_types: List[str] = field(
        default_factory=lambda: [
            "related_to",
            "is_a",
            "part_of",
            "prerequisite",
            "example_of",
            "contrasts_with",
            "causes",
            "used_in",
        ]
    )


@dataclass
class SearchConfig:
    """Search service configuration."""

    max_results: int = 50
    snippet_max_chars: int = 200
    snippet_context_chars: int = 50


@dataclass
class LoggingConfig:
    """Logging configuration."""

    level: str = field(default_factory=lambda: os.getenv("NEURONOTE_LOG_LEVEL", "INFO"))
    format: str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"
    file_path: Optional[str] = field(
        default_factory=lambda: os.getenv("NEURONOTE_LOG_FILE", "logs/neuronote.log")
    )
    max_file_size_mb: int = 10
    backup_count: int = 5


@dataclass
class AppConfig:
    """Top-level application configuration."""

    data_dir: str = field(
        default_factory=lambda: os.getenv(
            "NEURONOTE_DATA_DIR",
            str(Path.cwd() / "data"),
        )
    )
    upload_dir: str = field(default_factory=lambda: str(Path.cwd() / "data" / "uploads"))
    processed_dir: str = field(default_factory=lambda: str(Path.cwd() / "data" / "processed"))
    models_dir: str = field(
        default_factory=lambda: os.getenv(
            "NEURONOTE_MODEL_DIR",
            str(Path.cwd() / "models"),
        )
    )

    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    ocr: OCRConfig = field(default_factory=OCRConfig)
    stt: STTConfig = field(default_factory=STTConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    chunking: ChunkingConfig = field(default_factory=ChunkingConfig)
    knowledge_graph: KnowledgeGraphConfig = field(default_factory=KnowledgeGraphConfig)
    search: SearchConfig = field(default_factory=SearchConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)


# Global singleton configuration
config = AppConfig()
