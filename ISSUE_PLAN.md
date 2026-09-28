# Issue Plan

Hackathon: CPU-First Offline AI  
Project: NeuroNote - Offline Student Digital Brain

| ID | Issue | Assignee | Estimate | Due | Acceptance Criteria |
|---|---|---:|---:|---|---|
| NN-01 | Streamlit app shell and navigation | Frontend | 2h | Phase 2 | Dashboard, upload, search, graph, revision, quiz, progress, settings routes render without exceptions. |
| NN-02 | PDF ingestion and extraction | Backend | 3h | Phase 2 | PDF upload extracts text with PyMuPDF, stores source path, page metadata, and raw text in SQLite. |
| NN-03 | Image OCR path | Backend | 2h | Phase 2 | Images route through Tesseract OCR and degrade gracefully if OCR is unavailable. |
| NN-04 | Audio transcription path | Backend | 2h | Phase 2 | Audio route calls Whisper.cpp when installed and returns a clear pending/error message otherwise. |
| NN-05 | Local SLM JSON transformation | Backend | 4h | Phase 2 | llama.cpp + Phi-3 GGUF maps extracted text to subject/topic/concepts JSON, with heuristic fallback. |
| NN-06 | SQLite schema and CRUD | Backend | 2h | Phase 2 | Documents, concepts, graph edges, quizzes, revisions persist locally and tests pass. |
| NN-07 | Search by subject/topic/keyword | Full stack | 2h | Phase 2 | Search returns matching PDF source, page number when available, and relevant paragraph for keyword search. |
| NN-08 | Revision planner PDF-first flow | Frontend | 3h | Phase 2 | Revision displays mind map, definitions, questions, diagrams, and daily process from stored PDF data. |
| NN-09 | Quiz and answer evaluation | Full stack | 3h | Phase 2 | MCQ options are randomized; subjective answers show marks, feedback, missing concepts, and suggestions. |
| NN-10 | Knowledge graph | Backend | 2h | Phase 2 | NetworkX graph builds nodes/edges from stored concepts and renders in Streamlit. |
| NN-11 | Offline demo validation | QA | 2h | Phase 3 | Demo works with network disabled using local PDF input and SQLite output. |
| NN-12 | Repo audit and CI | QA | 3h | Phase 3 | GitLab CI runs at least 10 real checks: compile, lint, type, tests, smoke, PDF pipeline, schema, no-cloud scan, metadata, security, dependency audit. |
| NN-13 | Resource measurements | QA | 2h | Phase 3 | README records CPU/RAM measurement commands and expected demo evidence. |
| NN-14 | Model asset verification | Backend | 2h | Phase 3 | Valid Whisper and Phi-3 files are present locally; `scripts/local_audit.py model-manifest` passes before final demo. |
