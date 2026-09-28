# NeuroNote Backend

**Modular Python backend for offline-first, CPU-only AI document processing.**

## Overview

This backend provides a complete, production-ready Python API for processing unstructured educational content (PDFs, images, audio, text) into structured, searchable knowledge. It is designed to work completely offline with no cloud dependencies.

## Architecture

```
src/
├── api.py                    # Unified API facade
├── config.py                 # Configuration management
├── database/
│   ├── connection.py         # SQLite connection management
│   ├── schema.py             # Database schema (10 tables)
│   └── repository.py         # CRUD operations
├── ingestion/
│   └── pdf_extractor.py      # PDF text/image extraction
├── ocr/
│   └── processor.py          # Tesseract OCR with preprocessing
├── speech/
│   └── transcriber.py        # Whisper.cpp speech-to-text
├── llm/
│   └── engine.py             # llama.cpp + Phi-3 Mini inference
├── parser/
│   ├── text_processor.py     # Text cleaning and chunking
│   └── json_parser.py        # JSON validation and parsing
├── graph/
│   └── builder.py            # NetworkX knowledge graph
├── search/
│   └── engine.py             # SQLite FTS5 full-text search
├── services/
│   ├── processor.py          # Document processing orchestration
│   ├── quiz_service.py       # Quiz generation and management
│   └── revision_service.py   # Revision planning
├── utils/
│   ├── logging.py            # Logging configuration
│   ├── exceptions.py         # Custom exceptions
│   └── file_utils.py         # File handling utilities
└── models/                   # Data models (placeholder)
```

## Key Features

- **Offline-First**: Zero network calls, all processing local
- **CPU-Only**: Optimized for consumer hardware (4-core CPU, 8GB RAM)
- **Modular Design**: Each module is independent and testable
- **Clean API**: Single `NeuroNoteAPI` class for all operations
- **Type Hints**: Full type annotations for better IDE support
- **Logging**: Comprehensive logging with file and console handlers
- **Error Handling**: Custom exception hierarchy for precise error handling
- **Tested**: Unit tests for core modules

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install System Dependencies

**Tesseract OCR:**
- Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
- Linux: `sudo apt-get install tesseract-ocr`
- macOS: `brew install tesseract`

**Whisper.cpp:**
```bash
git clone https://github.com/ggerganov/whisper.cpp
cd whisper.cpp
make
```

**llama.cpp:**
```bash
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
make
```

### 3. Download Models

Place models in the `models/` directory:

- **Phi-3 Mini**: Download from HuggingFace (Phi-3-mini-4k-instruct-q4_k_m.gguf)
- **Whisper Small**: Download from HuggingFace (ggml-small-q5_0.bin)

### 4. Initialize Database

```bash
python database/__init__.py
```

### 5. Run Example

```bash
python scripts/example_usage.py
```

## API Usage

```python
from src.api import api

# Initialize
api.initialize()

# Process a document
result = api.upload_and_process(
    file_path="path/to/document.pdf",
    subject_name="Biology"
)

# Search
results = api.search(query="cell division", limit=10)

# Generate quiz
questions = api.generate_quiz(subject_id=1, count=10)

# Get knowledge graph
graph = api.get_knowledge_graph(subject_id=1)
```

## Configuration

All settings are managed via `src/config.py` and can be overridden with environment variables:

```bash
export NEURONOTE_DB_PATH=/path/to/database.db
export NEURONOTE_MODEL_DIR=/path/to/models
export LLM_MODEL_PATH=/path/to/phi-3-mini.gguf
export WHISPER_MODEL_PATH=/path/to/whisper.bin
export NEURONOTE_LOG_LEVEL=DEBUG
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/test_database.py -v
```

## Module Reference

### DocumentProcessor (`services/processor.py`)

Orchestrates the complete processing pipeline:
- PDF → Text extraction → LLM → Structured JSON → Database
- Image → OCR → LLM → Structured JSON → Database
- Audio → Whisper → LLM → Structured JSON → Database
- Text → Direct processing → LLM → Structured JSON → Database

### LLMEngine (`llm/engine.py`)

Wraps llama.cpp with Phi-3 Mini:
- Lazy model loading/unloading
- JSON extraction with retry logic
- Streaming support
- Memory-efficient inference

### SearchEngine (`search/engine.py`)

Full-text search using SQLite FTS5:
- Ranked search results
- Autocomplete suggestions
- Related term discovery
- Multi-type search (documents, definitions, questions)

### KnowledgeGraphBuilder (`graph/builder.py`)

NetworkX-based knowledge graph:
- TF-IDF similarity computation
- Automatic relationship detection
- Graph export for visualization

## Performance

| Operation | Expected Time (4-core CPU, 8GB RAM) |
|---|---|
| PDF extraction (50 pages) | < 30 seconds |
| OCR (1 page) | < 2 seconds |
| LLM inference (2048 tokens) | 10-20 seconds |
| Search query | < 2 seconds |
| Knowledge graph build (1000 concepts) | < 10 seconds |

## License

GPL-3.0

## Contributing

See main repository CONTRIBUTING.md