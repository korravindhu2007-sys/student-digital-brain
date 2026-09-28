# Offline PDF Study Workflow Tasks

## Implementation

- [x] Capture class, subject, and lesson metadata during PDF processing.
- [x] Extract PDF text locally with PyMuPDF.
- [x] Store document, concept, quiz, revision, and search data in SQLite.
- [x] Use local Ollama only when available.
- [x] Return local fallback study content when Ollama is unavailable.
- [x] Keep student PDF data local and out of hosted AI APIs.

## Verification

- [x] Cover backend PDF processing, search, quiz, revision, and dashboard behavior with tests.
- [x] Cover database schema expectations with tests.
- [x] Cover the end-to-end offline PDF pipeline with tests.
- [x] Include local audit checks for no-cloud-AI, SQLite schema, offline PDF, Streamlit pages, docs, and required files.
