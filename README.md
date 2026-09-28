# NeuroNote - Offline Student Digital Brain

![Version](https://img.shields.io/badge/version-0.3.1-blue)
![License](https://img.shields.io/badge/license-AGPL--3.0-green)
![Python](https://img.shields.io/badge/python-3.10%2B-yellow)
![Status](https://img.shields.io/badge/status-MVP-blue)

**Your Personal AI Learning Brain that works completely Offline.**

---

## Hackathon Compliance Snapshot

NeuroNote is a CPU-first, offline-first Streamlit application for transforming an uploaded study PDF into structured local knowledge using Ollama.

| Requirement | Status | Evidence |
|---|---|---|
| Offline-first core workflow | Implemented | PDF processing, Ollama inference, cache, and SQLite storage stay local. |
| CPU-first processing | Implemented | PyMuPDF, Tesseract OCR fallback, Ollama local models, SQLite. |
| No hosted AI APIs | Implemented | `scripts/local_audit.py no-cloud-ai` scans source code for cloud AI tokens. |
| Structured transformation | Implemented with fallback | Ollama generates JSON study notes, quiz, revision, and search answers from the uploaded PDF only. |
| Local storage | Implemented | `data/neuronote.db` SQLite database. |
| Graceful failure | Implemented | Missing PDF text/Ollama paths return user-visible status instead of crashing. |
| Repo audit | Implemented | `.gitlab-ci.yml`, `.pre-commit-config.yaml`, `scripts/local_audit.py`, coverage, security scan, and spec-kit files. |

Important final-demo note: Ollama must be running locally with a supported model such as `llama3`, `phi3`, `mistral`, or `gemma`.

```powershell
ollama serve
ollama pull phi3
uv run streamlit run app.py
```

---

## 📖 Project Overview

NeuroNote is an offline-first, CPU-based AI system designed for students to transform scattered educational material into a structured, searchable knowledge base. The system ingests PDFs, images, handwritten notes, audio recordings, and plain text, processes them entirely on-device using open-source AI models, and provides instant retrieval, revision planning, and quiz generation — all without any internet connection.

---

## ❗ Problem Statement

Students accumulate vast amounts of study material across multiple formats:

- PDF textbooks and research papers
- Handwritten class notes
- Lecture audio recordings
- Whiteboard photographs
- Digital text notes and assignments
- Scanned documents

During exam preparation, finding specific concepts, definitions, or connections across this scattered material becomes a significant challenge. Existing solutions either require cloud connectivity, compromise privacy, or fail to intelligently structure extracted knowledge.

---

## 💡 Solution

NeuroNote solves this by providing a completely offline, CPU-first pipeline that:

1. **Ingests** study PDFs
2. **Extracts** PDF text and page metadata locally
3. **Processes** content using a local Ollama model
4. **Structures** extracted knowledge into JSON and SQLite
5. **Caches** PDF and generated AI outputs to avoid repeated model calls
6. **Enables** semantic search, revision planning, and quiz generation from the PDF only

---

## ✨ Features

| Category | Feature | Description |
|---|---|---|
| **Input Processing** | PDF Extraction | Extract text and images from PDF documents using PyMuPDF |
| | OCR | Optical Character Recognition for handwritten/scanned text via Tesseract |
| **AI Processing** | Local Ollama | Concept extraction and knowledge structuring using local Ollama models |
| | JSON Structuring | Convert raw text into structured JSON with defined schemas |
| | Quiz Generation | Generate 20 MCQs with answers and explanations from the PDF |
| | Revision Companion | Generate mind map, important topics, notes, and question bank |
| **Storage** | SQLite Database | All data stored locally in a portable SQLite database |
| | Caching | Reuse previously processed PDFs, quizzes, revisions, and search answers |
| **Retrieval** | Semantic Search | Search subject, topic, keyword, concept, definition, and meaning with Ollama |
| **Learning Tools** | Revision Companion | Show progress, roadmap, study notes, and question bank |
| | Quiz Generator | Create PDF-only MCQs from the latest upload |
| **Privacy** | 100% Offline | No data ever leaves your machine |
| | No Cloud APIs | No hosted AI APIs or external inference services |
| | Local Storage | All data stored on your local machine |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User Interface                        │
│                      (Streamlit Web App)                      │
├──────────┬──────────┬──────────┬──────────┬─────────────────┤
│   PDF    │  Image   │  Audio   │   Text   │   Dashboard     │
│  Upload  │  Upload  │  Upload  │  Input   │   & Search      │
└────┬─────┴────┬─────┴────┬─────┴────┬─────┴────────┬────────┘
     │          │          │          │              │
     ▼          ▼          ▼          ▼              ▼
┌──────────────────────────────────────────────────────────────┐
│                    Processing Layer                           │
├──────────┬──────────┬──────────┬──────────────────────────────┤
│ PyMuPDF  │ Tesseract│Whisper.cpp│    Text Preprocessing       │
│ (PDF)    │  (OCR)   │  (STT)   │    (Cleaning, Chunking)     │
└──────────┴──────────┴──────────┴──────────────────────────────┘
               │                    │
               ▼                    ▼
┌──────────────────────────────────────────────────────────────┐
│                    AI Processing Layer                        │
├──────────────────────────────────────────────────────────────┤
│         llama.cpp + Phi-3 Mini GGUF                          │
│    (Concept Extraction, JSON Structuring,                    │
│     Knowledge Linking, Question Generation)                  │
└──────────────────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────┐
│                    Storage Layer                              │
├──────────────────────┬───────────────────────────────────────┤
│     SQLite Database   │      JSON Files                      │
│   (Documents, Topics, │   (Structured Knowledge              │
│    Definitions, Quiz  │    Export / Backup)                   │
│    History, etc.)     │                                       │
├──────────────────────┴───────────────────────────────────────┤
│                  Knowledge Graph (NetworkX)                   │
└──────────────────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────┐
│                    Retrieval Layer                            │
├──────────┬──────────┬──────────┬──────────┬─────────────────┤
│ Full-Text│  Topic   │ Concept  │ Revision │  Quiz Display   │
│  Search  │  Search  │  Search  │ Planner  │                 │
└──────────┴──────────┴──────────┴──────────┴─────────────────┘
```

---

## 🛠️ Technology Stack

| Technology | Purpose | Version |
|---|---|---|
| **Python** | Core programming language | 3.10+ |
| **Streamlit** | Web-based user interface | Latest |
| **SQLite** | Local database storage | Built-in |
| **Tesseract OCR** | OCR fallback for scanned PDF pages | Latest |
| **Ollama** | Local model runtime for all AI reasoning | Local |
| **PyMuPDF** | PDF text and image extraction | Latest |

---

## 📁 Folder Structure

```
student-digital-brain/
├── README.md                    # Project overview and documentation
├── LICENSE                      # AGPL-3.0 License
├── USER_MANUAL.md               # User-facing setup and workflow guide
├── AGENTS.md                    # Agent and maintainer operating notes
├── SPEC.md                      # Technical specification
├── CONTRIBUTING.md              # Contribution guidelines
├── CHANGELOG.md                 # Version history
├── .gitignore                   # Git ignore rules
├── SECURITY.md                  # Security and privacy policy
├── ISSUE_PLAN.md               # GitLab issue tracker plan
├── TEAM_PLAN.md                 # Team responsibilities and timeline
├── MILESTONES.md               # Project milestones
├── ROADMAP.md                   # Development roadmap
├── SYSTEM_DESIGN.md             # High-level system design
├── DEMO_PLAN.md                 # Demo sequence plan
├── PROJECT_CHECKLIST.md         # Project completion checklist
├── DECISIONS.md                 # Architectural decision records
├── docs/
│   ├── architecture.md          # Detailed system architecture
│   ├── workflow.md              # User workflow documentation
│   ├── database.md              # Database schema documentation
│   ├── ai_pipeline.md           # AI processing pipeline
│   ├── json_schema.md           # JSON schema definitions
│   ├── project_structure.md     # Detailed folder structure
│   └── future_scope.md          # Future roadmap and enhancements
├── src/                         # Application source code
│   └── __init__.py
├── models/                      # Local AI model files (GGUF)
├── database/                    # Database management module
│   └── __init__.py
├── data/                        # Application data (uploads, outputs)
│   ├── uploads/
│   ├── processed/
│   └── output/
├── assets/                      # Static assets (icons, images)
├── tests/                       # Unit tests and integration tests
│   └── __init__.py
├── scripts/                     # Utility scripts
└── examples/                    # Usage examples and sample data
```

---

## 🚀 Installation

### Prerequisites

```bash
# Python 3.10 or higher
python --version

# Tesseract OCR (install system package)
# Windows: Download from GitHub releases
# Linux: sudo apt install tesseract-ocr
# macOS: brew install tesseract

# Ollama local runtime and at least one model
ollama serve
ollama pull phi3
```

### Setup

```bash
# Clone the repository
git clone https://code.swecha.org/Bharatg/student-digital-brain.git
cd student-digital-brain

# Install dependencies
uv sync --dev

# Run the application
uv run streamlit run app.py
```

---

## Verification Commands

Run these checks before demo or submission:

```powershell
uv run python -m compileall app.py pages components services src tests scripts
uv run ruff check app.py pages components services src tests scripts
uv run mypy
uv run pytest
uv run python scripts/local_audit.py all
uv run bandit -q -r app.py pages components services src scripts
uv export --dev --format requirements-txt --no-hashes -o audit-requirements.txt
uv run pip-audit -r audit-requirements.txt
```

The GitLab pipeline runs real checks for compile, lint, type-check, tests, Streamlit smoke, offline PDF extraction, SQLite schema, no-cloud AI scan, metadata, security, and dependency audit.

---

## Offline Demo Flow

1. Disable Wi-Fi.
2. Start the app: `uv run streamlit run app.py`.
3. Upload a PDF in the Upload page.
4. Confirm the upload summary shows extracted characters and page count.
5. Search by subject, topic, and keyword.
6. Open/download the source PDF from Search and jump to the reported page.
7. Generate Revision content: mind map, definitions, questions, diagrams.
8. Generate a quiz and evaluate a written answer.
9. Confirm data persists in `data/neuronote.db`.

---

## Resource Evidence

During demo, capture CPU and memory from Windows Task Manager or PowerShell:

```powershell
Get-Process python | Select-Object ProcessName,CPU,WorkingSet64
```

Record the input file size, extracted character count, page count, SQLite row count, and CPU/RAM observed during processing.

---

## 🔮 Future Scope

| Phase | Feature | Description |
|---|---|---|
| **Phase 2** | MVP | Core pipeline: PDF upload, OCR, text extraction, basic search |
| **Phase 3** | AI Integration | LLM integration, concept extraction, JSON structuring, knowledge graph |
| **Phase 4** | Learning Tools | Quiz generator, revision planner, knowledge graph visualization |
| **Phase 5+** | Advanced Features | Multi-language support, handwriting recognition improvements, collaborative features, mobile adaptation |

---

## 📄 License

This project is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)**.

```
Copyright (C) 2026 NeuroNote Team

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
```

See [LICENSE](LICENSE) for the full license text.

---

## 👥 Team Members

| Member | Role | Responsibilities |
|---|---|---|
| **Member A** | Backend Developer | Database, OCR, LLM, Knowledge Graph, Testing |
| **Member B** | Frontend Developer | Streamlit UI, Audio, File Upload, Search, Dashboard, Documentation |

---

## 🙏 Acknowledgments

- [Streamlit](https://streamlit.io/) for the amazing web framework
- [llama.cpp](https://github.com/ggerganov/llama.cpp) for CPU-first LLM inference
- [Whisper.cpp](https://github.com/ggerganov/whisper.cpp) for offline speech recognition
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) for OCR capabilities
- [NetworkX](https://networkx.org/) for knowledge graph support
- [Phi-3 Mini](https://huggingface.co/microsoft/Phi-3-mini-4k-instruct) for local AI processing
- All open-source contributors who make offline AI possible
