# Offline PDF Study Workflow

## Problem

Students need to upload a textbook PDF and generate trustworthy study outputs without cloud APIs.

## Users

Class 5-12 students and hackathon reviewers evaluating offline AI behavior.

## Requirements

- Upload requires class, subject, and lesson/unit metadata.
- Search answers must come from the selected uploaded PDF lesson.
- Quiz questions must be generated from the PDF concepts and include answers and brief explanations.
- Revision must expose a mind map and practice question bank from extracted PDF sections.

## Offline Behavior

The workflow uses PyMuPDF, SQLite, and local Ollama. If Ollama is unavailable, the app returns a clear local fallback status instead of calling a cloud API.

## Acceptance Criteria

- Given a PDF with "biodiversity", when the student searches `biology / unit 1 / DIVERSITY`, then the answer cites the PDF excerpt.
- Given a processed PDF, when the student generates a quiz, then MCQs, assertion-reason, short, long, and HOTS questions are created from stored text.
- Given no internet connection, when Ollama and the model are already installed locally, then the workflow still runs.

