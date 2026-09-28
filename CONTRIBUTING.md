# Contributing

NeuroNote is built for the CPU-first offline AI hackathon. Contributions must preserve the local-only processing path.

## Rules

- Do not add OpenAI, Anthropic, hosted model APIs, telemetry, or cloud storage.
- Keep core processing runnable with Wi-Fi off.
- Use `pyproject.toml` and `uv`; do not add new dependency manifests.
- Keep model and upload artifacts out of git. `models/`, `tools/`, and `data/` are local runtime assets.
- Prefer CPU-safe libraries and quantized local runtimes.

## Local Setup

```powershell
uv sync --dev
uv run streamlit run app.py
```

## Required Checks

Run these before pushing:

```powershell
uv run python -m compileall app.py pages components services src tests scripts
uv run ruff check app.py pages components services src tests scripts
uv run mypy
uv run pytest
uv run python scripts/local_audit.py all
uv run bandit -q -r app.py pages components services src scripts
```

`scripts/local_audit.py model-manifest` checks local model files. It is required before the final offline demo, but model binaries are not committed.

## Commit Style

Use semantic commits:

- `feat: add PDF page search`
- `fix: preserve PDF metadata`
- `test: cover offline PDF pipeline`
- `docs: update hackathon runbook`
