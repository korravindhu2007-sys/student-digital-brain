from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
LOCAL_TESSERACT = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
LOCAL_WHISPER = ROOT_DIR / "tools" / "whisper.cpp" / "Release" / "whisper-cli.exe"
LOCAL_WHISPER_MODEL = ROOT_DIR / "models" / "whisper" / "ggml-base.en.bin"
LOCAL_LLAMA = ROOT_DIR / "tools" / "llama.cpp" / "llama-cli.exe"
LOCAL_PHI3 = ROOT_DIR / "models" / "phi3" / "Phi-3-mini-4k-instruct-q4.gguf"
MIN_PHI3_GGUF_BYTES = 2_000_000_000
DEFAULT_OLLAMA_HOST = "http://127.0.0.1:11434"
SUPPORTED_OLLAMA_MODELS = ("llama3", "llama3:latest", "llama3.2:1b", "phi3", "mistral", "gemma")


@dataclass(frozen=True)
class Settings:
    database_path: Path = Path("database/database.db")
    upload_dir: Path = Path("data/uploads")
    cache_dir: Path = Path("cache")
    log_dir: Path = Path("logs")
    output_dir: Path = Path("data/output")
    tesseract_cmd: str = "tesseract"
    whisper_cpp_cmd: str | None = None
    whisper_model_path: Path | None = None
    llama_cpp_cmd: str | None = None
    phi3_model_path: Path | None = None
    ollama_host: str = DEFAULT_OLLAMA_HOST
    ollama_model: str = "llama3:latest"
    chunk_size: int = 700
    chunk_overlap: int = 150
    logging_level: str = "INFO"
    max_upload_bytes: int = 100 * 1024 * 1024
    allowed_upload_extensions: tuple[str, ...] = (".pdf", ".png", ".jpg", ".jpeg")


def get_settings() -> Settings:
    model_path = os.getenv("NEURONOTE_PHI3_MODEL")
    whisper_model = os.getenv("NEURONOTE_WHISPER_MODEL")
    return Settings(
        database_path=Path(os.getenv("NEURONOTE_DB", os.getenv("NEURONOTE_DB_PATH", "database/database.db"))),
        upload_dir=Path(os.getenv("NEURONOTE_UPLOAD_DIR", "data/uploads")),
        cache_dir=Path(os.getenv("NEURONOTE_CACHE_DIR", "cache")),
        log_dir=Path(os.getenv("NEURONOTE_LOG_DIR", "logs")),
        output_dir=Path(os.getenv("NEURONOTE_OUTPUT_DIR", "data/output")),
        tesseract_cmd=os.getenv(
            "NEURONOTE_TESSERACT",
            str(LOCAL_TESSERACT) if LOCAL_TESSERACT.exists() else "tesseract",
        ),
        whisper_cpp_cmd=os.getenv(
            "NEURONOTE_WHISPER_CPP",
            str(LOCAL_WHISPER) if LOCAL_WHISPER.exists() else "",
        )
        or None,
        whisper_model_path=Path(whisper_model)
        if whisper_model
        else (LOCAL_WHISPER_MODEL if LOCAL_WHISPER_MODEL.exists() else None),
        llama_cpp_cmd=os.getenv(
            "NEURONOTE_LLAMA_CPP",
            str(LOCAL_LLAMA) if LOCAL_LLAMA.exists() else "",
        )
        or None,
        phi3_model_path=_usable_phi3_model(model_path),
        ollama_host=os.getenv("NEURONOTE_OLLAMA_HOST", DEFAULT_OLLAMA_HOST).rstrip("/"),
        ollama_model=os.getenv("NEURONOTE_OLLAMA_MODEL", "llama3:latest"),
        chunk_size=int(os.getenv("NEURONOTE_CHUNK_SIZE", "700")),
        chunk_overlap=int(os.getenv("NEURONOTE_CHUNK_OVERLAP", "150")),
        logging_level=os.getenv("NEURONOTE_LOG_LEVEL", "INFO"),
    )


def _usable_phi3_model(model_path: str | None) -> Path | None:
    candidate = Path(model_path) if model_path else LOCAL_PHI3
    if not candidate.exists():
        return None
    if candidate.stat().st_size < MIN_PHI3_GGUF_BYTES:
        return None
    return candidate
