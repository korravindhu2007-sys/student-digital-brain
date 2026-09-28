# NeuroNote – Technical Specification

**Version:** 1.0.0  
**Status:** Planning  
**Last Updated:** 2026-06-28

---

## Project Objective

Develop a completely offline, CPU-first AI application that transforms unstructured student educational content (PDFs, images, handwritten notes, audio recordings, and text notes) into a structured, searchable knowledge base stored in SQLite, enabling instant retrieval, revision planning, quiz generation, and knowledge graph visualization — all without any internet connection or cloud API dependency.

---

## Problem Statement

Students accumulate study material across multiple formats: PDF textbooks, handwritten class notes, lecture audio recordings, whiteboard photographs, digital text notes, and assignments. During exam preparation, finding specific concepts or connections across this scattered material is inefficient. Existing solutions require cloud connectivity, compromise privacy, or fail to intelligently structure extracted knowledge into an interconnected format.

---

## Scope

| In Scope | Out of Scope |
|---|---|
| PDF text and image extraction | Cloud-based AI inference |
| OCR for printed and handwritten text | GPU-accelerated processing |
| Speech-to-text for audio recordings | Real-time transcription |
| Concept extraction via local LLM | Multi-user collaboration |
| SQLite storage and full-text search | Mobile application |
| Knowledge graph construction | Web deployment |
| Quiz and revision plan generation | API access |
| CPU-only inference | External service integration |

---

## Target Users

| User Type | Description | Needs |
|---|---|---|
| **Students (Primary)** | High school, undergraduate, and graduate students | Organize lecture notes, textbooks, and study materials for exam preparation |
| **Self-learners** | Individuals studying independently | Structure diverse learning resources into a coherent knowledge base |
| **Researchers** | Academic researchers with large PDF collections | Extract and connect concepts across research papers |

---

## Functional Requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-01 | System shall accept PDF files up to 100 MB for text and image extraction | High |
| FR-02 | System shall accept JPEG, PNG, and TIFF images for OCR processing | High |
| FR-03 | System shall accept MP3, WAV, and M4A audio files for speech-to-text | High |
| FR-04 | System shall accept plain text input via direct text entry or file upload | High |
| FR-05 | System shall perform OCR on images using Tesseract with image preprocessing | High |
| FR-06 | System shall transcribe audio using Whisper.cpp on CPU | High |
| FR-07 | System shall process extracted text through a local LLM (Phi-3 Mini) for concept extraction | High |
| FR-08 | System shall output structured JSON from the LLM pipeline | High |
| FR-09 | System shall store all structured data in a local SQLite database | High |
| FR-10 | System shall provide full-text search across all processed content | High |
| FR-11 | System shall generate multiple-choice and short-answer quiz questions | Medium |
| FR-12 | System shall build a knowledge graph connecting related concepts across documents | Medium |
| FR-13 | System shall generate a revision plan based on topics and available time | Medium |
| FR-14 | System shall visualize the knowledge graph interactively | Medium |
| FR-15 | System shall support batch upload of multiple files | Low |

---

## Non-Functional Requirements

| ID | Requirement | Target |
|---|---|---|
| NFR-01 | PDF ingestion time | < 30 seconds per 100 pages |
| NFR-02 | OCR processing time | < 2 seconds per page |
| NFR-03 | LLM inference time | < 10 seconds per chunk |
| NFR-04 | Search response time | < 2 seconds |
| NFR-05 | Peak RAM usage | < 8 GB |
| NFR-06 | Database growth | < 50 MB per 1000 documents |
| NFR-07 | Model storage size | < 4 GB for all models |
| NFR-08 | Operating system compatibility | Windows 10+, Linux, macOS 12+ |
| NFR-09 | Python version | 3.10, 3.11, 3.12 |
| NFR-10 | Offline functionality | 100% — no internet required |

---

## Supported Inputs

| Input Type | Formats | Max Size | Processing Engine |
|---|---|---|---|
| PDF Documents | .pdf | 100 MB | PyMuPDF |
| Images (printed) | .jpg, .jpeg, .png, .tiff | 50 MB | Tesseract OCR |
| Images (handwritten) | .jpg, .jpeg, .png | 50 MB | Tesseract OCR with preprocessing |
| Images (whiteboard) | .jpg, .jpeg, .png | 50 MB | Tesseract OCR with contrast enhancement |
| Audio Recordings | .mp3, .wav, .m4a | 500 MB | Whisper.cpp |
| Plain Text | .txt, .md, direct input | 10 MB | Direct processing |

---

## Expected Outputs

| Output | Description | Format |
|---|---|---|
| Structured Knowledge | Extracted concepts, definitions, topics with relationships | JSON |
| Database Records | Persistent storage in local SQLite database | SQLite |
| Search Results | Ranked, filterable results with context snippets | Streamlit UI |
| Knowledge Graph | Interactive visualization of concept relationships | NetworkX + HTML |
| Quiz Questions | Multiple-choice and short-answer questions | JSON + UI |
| Revision Plan | Day-by-day study schedule organized by topic | Markdown + UI |
| Export File | Complete knowledge base export for backup | JSON |

---

## AI Processing Pipeline

```
Raw Input (PDF/Image/Audio/Text)
         │
         ▼
┌─────────────────────────────────┐
│ Step 1: Format-Specific        │
│ Extraction                     │
│                                │
│ PDF  → PyMuPDF → Text + Images │
│ Image→ Tesseract → OCR Text   │
│ Audio→ Whisper.cpp → Transcript│
│ Text → Direct Input            │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│ Step 2: Text Preprocessing     │
│                                │
│ • Clean whitespace & artifacts │
│ • Normalize encoding (UTF-8)   │
│ • Split into 2048-token chunks │
│ • Add 256-token overlap        │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│ Step 3: LLM Inference          │
│                                │
│ For each chunk:                │
│ • Build extraction prompt      │
│ • Run Phi-3 Mini via llama.cpp │
│   (temperature: 0.3)          │
│ • Collect raw JSON output      │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│ Step 4: JSON Validation        │
│                                │
│ • Parse JSON from LLM output  │
│ • Validate against schema      │
│ • Retry on failure (max 3)    │
│ • Aggregate across chunks     │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│ Step 5: Knowledge Linking      │
│                                │
│ • Match concepts via TF-IDF    │
│ • Create relationship edges    │
│ • Update NetworkX graph        │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│ Step 6: Storage                │
│                                │
│ • Save to SQLite tables        │
│ • Update FTS5 search index     │
│ • Serialize graph edges        │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│ Step 7: Retrieval Ready        │
│                                │
│ • Enable search for new content│
│ • Update dashboard statistics  │
└─────────────────────────────────┘
```

---

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    USER INTERFACE                            │
│                    (Streamlit)                               │
│  Upload │ Search │ Quiz │ Graph │ Dashboard                  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                          │
│  File Controller │ Search Engine │ Session State Manager     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    SERVICE LAYER                              │
│  PDF    │  OCR    │  STT    │  LLM    │  KG    │  Quiz      │
│  Service│  Service│  Service│  Service│  Service│  Service   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    DATA LAYER                                 │
│  SQLite Database │ File System │ NetworkX Knowledge Graph    │
└─────────────────────────────────────────────────────────────┘
```

---

## JSON Output Schema

Each document processed by the LLM produces the following JSON structure:

```json
{
  "document": {
    "title": "Cell_Biology_Chapter_5",
    "subject": "Biology",
    "source_type": "pdf"
  },
  "concepts": [
    {
      "term": "Mitosis",
      "definition": "The process of cell division resulting in two identical daughter cells.",
      "importance": "high",
      "related_concepts": ["Cell Cycle", "Meiosis", "Chromosome"]
    },
    {
      "term": "Meiosis",
      "definition": "Cell division producing four genetically distinct daughter cells.",
      "importance": "high",
      "related_concepts": ["Mitosis", "Gametes", "Crossing Over"]
    }
  ],
  "topics": [
    {
      "name": "Cell Division",
      "description": "Processes of mitotic and meiotic cell division",
      "subtopics": ["Mitosis Phases", "Meiosis Phases"]
    }
  ],
  "questions": [
    {
      "question": "What is the primary function of mitosis?",
      "answer": "Growth and repair of body cells",
      "options": ["Production of gametes", "Growth and repair of body cells", "Reduction of chromosome count", "Crossing over genetic material"],
      "type": "multiple_choice",
      "difficulty": "easy"
    }
  ]
}
```

---

## SQLite Database Design

The system uses 10 tables to store all structured knowledge:

| Table | Purpose | Key Columns |
|---|---|---|
| **documents** | Uploaded file metadata and raw text | id, title, file_type, status, raw_text |
| **subjects** | Academic subject categories | id, name, description |
| **topics** | Topics within subjects | id, name, subject_id, parent_topic_id |
| **definitions** | Extracted concepts and terms | id, term, definition, subject_id, topic_id, importance |
| **questions** | Generated quiz questions | id, question_text, answer, options, type, difficulty |
| **audio** | Processed audio metadata | id, document_id, transcript, duration_seconds |
| **images** | Processed image metadata | id, document_id, ocr_text, image_type, ocr_confidence |
| **knowledge_links** | Concept relationship edges | id, source_concept_id, target_concept_id, relationship_type, weight |
| **quiz_history** | Completed quiz records | id, subject_id, score_percentage, questions (JSON), taken_at |
| **revision_history** | Planned revision sessions | id, subject_id, planned_date, duration_minutes, completed |

Full-text search is enabled via SQLite FTS5 on the documents table.

---

## Offline-First Design

| Principle | Implementation |
|---|---|
| Zero Network Calls | No HTTP requests to any external API |
| Local Model Storage | All AI models stored in `models/` directory (gitignored) |
| Local Database | All data stored in local SQLite database file |
| No Telemetry | No analytics, crash reporting, or usage tracking |
| No Registration | No user accounts, email, or passwords required |
| No CDN Assets | All UI assets bundled with the application |
| Air-Gap Functional | System works 100% without any internet connectivity |

---

## CPU-First Design

| Principle | Implementation |
|---|---|
| No GPU Required | All inference uses CPU-optimized libraries (llama.cpp, Whisper.cpp) |
| Quantized Models | All models use 4-bit quantization (Q4_K_M) reducing memory by ~60% |
| Efficient Chunking | Documents split into 2048-token chunks fitting within 4K context window |
| Lazy Loading | Models loaded on demand, unloaded after inference to save RAM |
| Thread Optimization | Inference uses 4 CPU threads by default |
| Progressive Processing | Documents processed sequentially with user-visible progress |

**Expected Performance on Typical Student Laptop (4-core CPU, 8 GB RAM):**

| Model | RAM Usage | Speed |
|---|---|---|
| Phi-3 Mini (3.8B, Q4_K_M) | ~3.5 GB | 10-20 tokens/second |
| Whisper ggml-small | ~1.5 GB | ~3x real-time |

---

## Assumptions

| # | Assumption |
|---|---|
| A-01 | User has Python 3.10 or higher installed |
| A-02 | User has at least 8 GB of RAM available |
| A-03 | User has at least 10 GB of free disk space |
| A-04 | Tesseract OCR is installed on the system |
| A-05 | User has internet access for initial model download (~3 GB) |
| A-06 | Input documents are primarily in English |
| A-07 | PDF documents are not encrypted or password-protected |
| A-08 | Audio recordings are reasonably clear (minimal background noise) |
| A-09 | User has basic familiarity with command-line tools |
| A-10 | User is running on a 64-bit operating system |

---

## Limitations

| # | Limitation |
|---|---|
| L-01 | Handwriting OCR accuracy is limited (60-85%) compared to printed text (>95%) |
| L-02 | LLM inference speed is capped at 10-30 tokens/second on consumer CPUs |
| L-03 | Context window limited to 4096 tokens (documents must be chunked) |
| L-04 | Single-user application — no collaborative features |
| L-05 | No real-time transcription — audio processed after upload |
| L-06 | English language focused initially; multi-language support requires configuration |
| L-07 | Database performance degrades beyond ~10,000 documents |
| L-08 | Knowledge graph is rebuilt on each application restart |

---

## Future Enhancements

| Enhancement | Priority | Description |
|---|---|---|
| Multi-language OCR | Medium | Support for non-English languages in Tesseract |
| Handwriting Recognition Model | Low | Replace Tesseract with dedicated HTR model for >90% accuracy |
| Fine-tuned Educational LLM | Low | Fine-tune Phi-3 Mini on textbook corpus for better extraction |
| Mobile Companion App | Low | React Native app for camera scanning and voice notes |
| Collaborative Study Groups | Low | LAN-based shared knowledge base for study groups |
| Anki Integration | Low | Export concepts as Anki flashcard decks |
| Docker Deployment | Low | Containerized setup for reproducible environment |

---

## Success Criteria

| Criteria | Target |
|---|---|
| PDF document processed end-to-end | < 60 seconds for a 50-page textbook chapter |
| Concept extraction accuracy | > 80% of key concepts identified correctly |
| Search results returned | < 2 seconds for any query |
| Quiz questions generated | Valid, answerable questions with correct answers |
| Knowledge graph visualization | Interactive display with clickable nodes |
| Offline operation | All features functional without internet |
| CPU-only processing | No GPU required for any operation |