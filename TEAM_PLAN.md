# NeuroNote – Team Plan

**Version:** 1.0.0  
**Last Updated:** 2026-06-28

---

## Team Structure

| Aspect | Detail |
|---|---|
| **Team Size** | 2 Members |
| **Hackathon** | CPU-First Offline AI Hackathon |
| **Project** | NeuroNote – Offline Student Digital Brain |

---

## Member Responsibilities

### Member A — Backend Developer

| Area | Specific Responsibilities | Technologies |
|---|---|---|
| **OCR Pipeline** | Image preprocessing (grayscale, binarization, denoising, deskewing), Tesseract integration, text extraction from handwritten and printed images | Tesseract, OpenCV, pytesseract |
| **Database** | SQLite schema design (10 tables), connection manager, FTS5 full-text search, query optimization, data persistence | SQLite, sqlite3 |
| **LLM Integration** | llama.cpp Python bindings, Phi-3 Mini model loading and inference, prompt engineering, context window management, memory optimization | llama.cpp, Phi-3 Mini GGUF |
| **Knowledge Graph** | NetworkX graph construction, TF-IDF similarity computation, relationship edge creation, graph serialization | NetworkX, scikit-learn |
| **Testing** | Unit tests for processing and AI modules, integration tests for end-to-end workflows, performance benchmarking | pytest, pytest-cov |

### Member B — Frontend Developer

| Area | Specific Responsibilities | Technologies |
|---|---|---|
| **Streamlit UI** | Main application entry point, dashboard with statistics, multi-page navigation, session state management | Streamlit |
| **File Upload** | Drag-and-drop interface, file validation (type, size), metadata input, batch upload support, progress indicators | Streamlit |
| **Audio Processing** | Audio file upload interface, Whisper.cpp integration UI, transcription status display | Streamlit, Whisper.cpp |
| **Dashboard** | System statistics display, recent activity feed, subject breakdown, quick navigation links | Streamlit |
| **Documentation** | README, SPEC, setup guides, user documentation, inline code documentation | Markdown |
| **Testing** | UI component tests, user workflow validation, cross-browser compatibility | pytest, Streamlit testing |

---

## Timeline

| Week | Member A (Backend) | Member B (Frontend) |
|---|---|---|
| **Week 1** | Repository setup, Python environment, requirements.txt, folder structure | Streamlit scaffold, dashboard page, sidebar navigation |
| | OCR pipeline with Tesseract integration | File upload interface with drag-and-drop |
| | Whisper.cpp integration for audio transcription | Metadata input and validation |
| **Week 2** | SQLite schema design and initialization | Full-text search interface with filters |
| | llama.cpp integration with Phi-3 Mini | Quiz generation and taking interface |
| | PDF processing with PyMuPDF | Knowledge graph visualization |
| | Concept extraction and JSON structuring | Revision planner interface |
| **Week 3** | Knowledge graph construction with NetworkX | Documentation finalization |
| | Unit tests for all backend modules | Demo script writing |
| | Integration tests for end-to-end workflows | Demo video recording and editing |
| | Performance optimization and benchmarking | Offline functionality verification |

---

## Milestones

| Milestone | Target Date | Deliverable |
|---|---|---|
| **M1 — Project Setup Complete** | Week 1, Day 1 | Repository initialized, dependencies installed, folder structure ready |
| **M2 — Core Processing Functional** | Week 1, Day 4 | PDF extraction, OCR, and audio transcription working with Streamlit upload |
| **M3 — Database Operational** | Week 2, Day 1 | All 10 SQLite tables created, FTS5 search index active |
| **M4 — AI Pipeline Integrated** | Week 2, Day 3 | LLM extracts concepts from text, JSON structured output stored in database |
| **M5 — All Features Complete** | Week 3, Day 1 | Search, knowledge graph, quiz generator, and revision planner fully functional |
| **M6 — Testing Complete** | Week 3, Day 2 | All unit and integration tests pass, >80% code coverage |
| **M7 — Submission Ready** | Week 3, Day 3 | Documentation finalized, demo video recorded, offline verification passed |

---

## Communication Plan

| Method | Frequency | Purpose |
|---|---|---|
| **Daily Standup** | 15 minutes, every morning | Progress update, blockers, plan for the day |
| **GitLab Issues** | As needed | Task tracking, bug reports, feature requests |
| **Code Review** | Every merge request | Ensure code quality and consistency |
| **Weekly Sync** | 30 minutes, every Friday | Milestone review, adjust priorities, plan next week |
| **Instant Messaging** | As needed | Quick questions, clarifications, sharing resources |

---

## Risk Management

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| **llama.cpp integration is more complex than expected** | Medium | High | Start integration early (Week 1). Have a fallback to test with a simpler model. Allocate buffer time. |
| **OCR quality on handwriting is too low** | Medium | High | Implement multiple preprocessing paths. Allow manual text correction in UI. Have alternative input method (type instead of scan). |
| **LLM inference too slow on low-end hardware** | Medium | Medium | Optimize chunk size. Test smaller quantized models. Implement caching. Display estimated processing time to users. |
| **Streamlit limitations for complex UI** | Low | Medium | Prototype key components early. Have alternative visualization libraries (Plotly) ready. Keep UI design within Streamlit capabilities. |
| **Team member unavailable due to other commitments** | Low | High | Cross-train on critical components. Document all code clearly. Maintain shared understanding of architecture. |

---

## Contribution Strategy

| Principle | Practice |
|---|---|
| **Branch Strategy** | Feature branches from `develop`. Merge to `main` only at milestones. |
| **Commit Convention** | Conventional Commits format: `feat:`, `fix:`, `docs:`, `test:` |
| **Code Review** | Every merge request reviewed by the other team member before merging |
| **Documentation** | Document as you code. Update README and inline docs with each feature. |
| **Testing** | Write tests alongside code. Never merge untested code. |
| **Offline Verification** | Test every feature with network disabled before marking complete. |