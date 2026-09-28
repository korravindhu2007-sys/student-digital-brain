# NeuroNote Constitution

## Principles

1. Offline-first: core learning workflows must run without hosted AI services.
2. CPU-first: processing should remain usable on standard student laptops.
3. PDF-grounded answers: search, quiz, and revision outputs must be traceable to uploaded study material.
4. Local persistence: structured data belongs in local SQLite storage.
5. Student focus: workflows should support class 5-12 study and Class 11 Biology practice.

## Quality Gates

- Formatting, linting, typing, tests, coverage, security, and local audits must pass before merge.
- Any new AI workflow must include graceful fallback behavior when Ollama is unavailable.

