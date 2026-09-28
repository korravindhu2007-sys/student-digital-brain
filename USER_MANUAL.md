# NeuroNote User Manual

## Purpose

NeuroNote helps students turn an uploaded textbook PDF into searchable notes, revision material, and practice questions while keeping processing local.

## Setup

1. Install Python 3.10 or newer.
2. Install `uv`.
3. Install Ollama and pull a supported local model such as `phi3` or `llama3`.
4. Run `uv sync --dev`.
5. Start the app with `uv run streamlit run app.py`.

## Workflow

1. Open the Upload page.
2. Upload a PDF.
3. Enter class, subject, and lesson/unit.
4. Use Search to ask for a keyword from that PDF lesson.
5. Use Quiz to generate level-wise practice questions.
6. Use Revision to review the extracted mind map and question bank.

## Offline Notes

The app stores data in SQLite under `data/`. Ollama must already have a model downloaded before working without internet.

