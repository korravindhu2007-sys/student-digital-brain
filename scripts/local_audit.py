from __future__ import annotations

import argparse
import json
import os
import subprocess  # nosec B404
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIRS = [ROOT / "app.py", ROOT / "pages", ROOT / "components", ROOT / "services", ROOT / "src", ROOT / "tests"]
FORBIDDEN_CLOUD_TOKENS = ("openai", "anthropic", "api_key", "cuda", "torch.cuda")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run real local audit checks for the CPU-first hackathon.")
    parser.add_argument(
        "check",
        choices=[
            "all",
            "required-files",
            "license",
            "no-cloud-ai",
            "package-imports",
            "sqlite-schema",
            "offline-pdf",
            "streamlit-pages",
            "model-manifest",
            "gitignore",
            "docs-commands",
        ],
    )
    args = parser.parse_args()
    checks = {
        "required-files": check_required_files,
        "license": check_license,
        "no-cloud-ai": check_no_cloud_ai,
        "package-imports": check_package_imports,
        "sqlite-schema": check_sqlite_schema,
        "offline-pdf": check_offline_pdf,
        "streamlit-pages": check_streamlit_pages,
        "model-manifest": check_model_manifest,
        "gitignore": check_gitignore,
        "docs-commands": check_docs_commands,
    }
    selected = (
        {name: fn for name, fn in checks.items() if name != "model-manifest"}
        if args.check == "all"
        else {args.check: checks[args.check]}
    )
    for name, fn in selected.items():
        fn()
        print(f"PASS {name}")
    return 0


def check_required_files() -> None:
    required = [
        "README.md",
        "SPEC.md",
        "ISSUE_PLAN.md",
        "TEAM_PLAN.md",
        "CONTRIBUTING.md",
        "CHANGELOG.md",
        "LICENSE",
        "pyproject.toml",
        ".gitlab-ci.yml",
        ".pre-commit-config.yaml",
        "USER_MANUAL.md",
        "AGENTS.md",
        "SECURITY.md",
        "CODE_OF_CONDUCT.md",
        ".env.example",
        ".editorconfig",
        "Dockerfile",
        ".dockerignore",
    ]
    missing = [name for name in required if not (ROOT / name).exists()]
    _require(not missing, f"Missing required files: {missing}")


def check_license() -> None:
    text = (ROOT / "LICENSE").read_text(encoding="utf-8", errors="ignore")
    _require("GNU AFFERO GENERAL PUBLIC LICENSE" in text, "LICENSE must be AGPL.")
    _require("Version 3" in text, "LICENSE must be GPL version 3.")


def check_no_cloud_ai() -> None:
    offenders: list[str] = []
    for path in _source_files():
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        for token in FORBIDDEN_CLOUD_TOKENS:
            if token in text:
                offenders.append(f"{path.relative_to(ROOT)} contains {token}")
    _require(not offenders, "\n".join(offenders))


def check_package_imports() -> None:
    sys.path.insert(0, str(ROOT / "src"))
    import fitz  # noqa: F401
    import streamlit  # noqa: F401

    import neuronote.api  # noqa: F401


def check_sqlite_schema() -> None:
    sys.path.insert(0, str(ROOT / "src"))
    from neuronote.database import get_connection

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        db_path = Path(tmp) / "audit.db"
        with get_connection(db_path) as conn:
            tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    required = {
        "documents",
        "chunks",
        "study_notes",
        "flashcards",
        "formula_sheet",
        "highlights",
        "chat_history",
        "cache",
    }
    _require(required.issubset(tables), f"SQLite schema missing: {required - tables}")


def check_offline_pdf() -> None:
    sys.path.insert(0, str(ROOT / "src"))
    import fitz

    from neuronote.api import process_document, search_keyword

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        tmp_path = Path(tmp)
        os.environ["NEURONOTE_UPLOAD_DIR"] = str(tmp_path / "uploads")
        os.environ["NEURONOTE_PHI3_MODEL"] = str(tmp_path / "missing-model.gguf")
        db_path = tmp_path / "audit.db"
        pdf_path = tmp_path / "audit.pdf"
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "DBMS Normalization removes redundancy. BCNF is a database normal form.")
        doc.save(pdf_path)
        doc.close()

        result = process_document(pdf_path, {"subject": "DBMS", "topic": "Normalization"}, db_path=db_path)
        hits = search_keyword("BCNF", db_path=db_path)
        _require(result["ok"] is True, "PDF processing failed.")
        _require(int(result["extracted_chars"]) > 20, "PDF text extraction returned too little text.")
        _require(int(result["page_count"]) == 1, "PDF page metadata was not saved.")
        _require(bool(hits and hits[0].get("present")), "Semantic search did not find the PDF term.")


def check_streamlit_pages() -> None:
    page_paths = [
        "app.py",
        "pages/dashboard.py",
        "pages/upload.py",
        "pages/settings.py",
    ]
    code = (
        "from streamlit.testing.v1 import AppTest\n"
        f"paths = {page_paths!r}\n"
        "for path in paths:\n"
        "    app = AppTest.from_file(path)\n"
        "    app.run(timeout=20)\n"
        "    assert not app.exception, (path, app.exception)\n"
    )
    _run([sys.executable, "-c", code])


def check_model_manifest() -> None:
    sys.path.insert(0, str(ROOT / "src"))
    from neuronote.config import SUPPORTED_OLLAMA_MODELS, get_settings
    from neuronote.ollama import ollama_status

    settings = get_settings()
    status = ollama_status()
    report = {
        "ollama_host": settings.ollama_host,
        "configured_model": settings.ollama_model,
        "supported_models": list(SUPPORTED_OLLAMA_MODELS),
        "ollama_available": status["available"],
        "installed_models": status["models"],
    }
    (ROOT / "MODEL_STATUS.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    _require(
        settings.ollama_model in SUPPORTED_OLLAMA_MODELS, "Configured Ollama model is not in the supported demo list."
    )
    _require(bool(status["available"]), "Ollama is not reachable. Run `ollama serve` before the final demo.")


def check_gitignore() -> None:
    text = (ROOT / ".gitignore").read_text(encoding="utf-8", errors="ignore")
    for item in ["data/", "models/", "tools/", ".venv/", ".uv-cache/"]:
        _require(item in text, f".gitignore must ignore {item}")


def check_docs_commands() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8", errors="ignore")
    _require("uv run streamlit run app.py" in readme, "README must include the Streamlit run command.")
    _require("uv run pytest" in readme, "README must include the pytest command.")
    _require("scripts/local_audit.py all" in readme, "README must include the local audit command.")


def _source_files() -> list[Path]:
    files: list[Path] = []
    for item in SRC_DIRS:
        if item.is_file() and item.suffix == ".py":
            files.append(item)
        elif item.is_dir():
            files.extend(path for path in item.rglob("*.py") if ".venv" not in path.parts)
    return files


def _run(command: list[str]) -> None:
    completed = subprocess.run(command, cwd=ROOT, check=False)  # nosec B603
    _require(completed.returncode == 0, f"Command failed: {' '.join(command)}")


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


if __name__ == "__main__":
    raise SystemExit(main())
