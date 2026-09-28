# Agent Guide

## Project Rules

- Preserve offline-first behavior.
- Do not add hosted AI APIs.
- Keep student PDF data local.
- Prefer local Ollama and SQLite-backed workflows.
- Run the CI-equivalent PowerShell checks before pushing.

## Current Verification Commands

```powershell
uv run ruff format --check app.py pages components services src/neuronote tests/test_backend_api.py tests/test_database.py tests/test_e2e_backend.py scripts
uv run ruff check app.py pages components services src/neuronote tests/test_backend_api.py tests/test_database.py tests/test_e2e_backend.py scripts
uv run mypy
uv run pytest
uv run python scripts/local_audit.py all
```

## Push Policy

Push changes to GitLab only unless the user explicitly asks for GitHub.

