# Offline PDF Study Workflow Plan

## Scope

Complete the offline study path that accepts a student PDF, extracts text locally, stores structured learning data in SQLite, and serves search, quiz, and revision workflows without hosted AI APIs.

## Data Flow

PDF upload with class, subject, and lesson metadata -> PyMuPDF text extraction -> local chunking and concept generation -> SQLite persistence -> search, quiz, dashboard, and revision views.

## Local Dependencies

- PyMuPDF for PDF parsing.
- SQLite for documents, concepts, quizzes, revisions, and search cache.
- Ollama for optional local generation when available.
- Local fallback responses when Ollama or the configured model is unavailable.

## Verification

- `uv run ruff format --check app.py pages components services src/neuronote tests/test_backend_api.py tests/test_database.py tests/test_e2e_backend.py scripts`
- `uv run ruff check app.py pages components services src/neuronote tests/test_backend_api.py tests/test_database.py tests/test_e2e_backend.py scripts`
- `uv run mypy`
- `uv run pytest`
- `uv run python scripts/local_audit.py all`
