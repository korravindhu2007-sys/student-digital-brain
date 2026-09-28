from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .database import keyword_search, search_concepts, search_documents


def _format_result(row: dict[str, Any], score: int = 90) -> dict[str, Any]:
    metadata = _load_metadata(row)
    page_match = _find_page_match(metadata.get("pages", []), row.get("concept") or row.get("topic"))
    return {
        "id": f"concept-{row['id']}",
        "title": row["concept"],
        "subject": row["subject"],
        "topic": row["topic"],
        "source": row.get("source_name", "unknown"),
        "source_type": row.get("source_type", "text"),
        "score": score,
        "snippet": row["definition"],
        "page": page_match.get("page"),
        "source_path": metadata.get("source_path", ""),
        "pages": metadata.get("pages", []),
        "assets": metadata.get("assets", {}),
        "match_type": "concept",
        "document_id": row.get("document_id"),
        "backend_response": row,
    }


def _format_document_result(row: dict[str, Any], keyword: str | None = None, score: int = 80) -> dict[str, Any]:
    metadata = _load_metadata(row)
    page_match = _find_page_match(metadata.get("pages", []), keyword)
    snippet = page_match.get("paragraph") or _matching_paragraph(row.get("raw_text", ""), keyword)
    return {
        "id": f"document-{row['id']}",
        "title": row["source_name"],
        "subject": row["subject"],
        "topic": row["topic"],
        "source": row["source_name"],
        "source_type": row["source_type"],
        "score": score,
        "snippet": snippet,
        "page": page_match.get("page"),
        "source_path": metadata.get("source_path", ""),
        "pages": metadata.get("pages", []),
        "assets": metadata.get("assets", {}),
        "match_type": "document",
        "document_id": row["id"],
        "backend_response": row,
    }


def search_by_topic(topic: str, db_path: Path | None = None) -> list[dict[str, Any]]:
    concept_results = [_format_result(row, 92) for row in search_concepts("topic", topic, db_path)]
    document_results = [
        _format_document_result(row, topic, 86) for row in search_documents(topic=topic, db_path=db_path)
    ]
    return concept_results + document_results


def search_by_subject(subject: str, db_path: Path | None = None) -> list[dict[str, Any]]:
    concept_results = [_format_result(row, 88) for row in search_concepts("subject", subject, db_path)]
    document_results = [
        _format_document_result(row, subject, 82) for row in search_documents(subject=subject, db_path=db_path)
    ]
    return concept_results + document_results


def search_by_keyword(keyword: str, db_path: Path | None = None) -> list[dict[str, Any]]:
    concept_results = [_format_result(row, 95) for row in keyword_search(keyword, db_path)]
    document_results = [
        _format_document_result(row, keyword, 90) for row in search_documents(keyword=keyword, db_path=db_path)
    ]
    return concept_results + document_results


def _matching_paragraph(text: str, keyword: str | None = None, max_chars: int = 500) -> str:
    paragraphs = [part.strip() for part in text.replace("\r\n", "\n").split("\n\n") if part.strip()]
    if not paragraphs:
        paragraphs = [text.strip()] if text.strip() else []
    if keyword:
        keyword_lower = keyword.lower()
        for paragraph in paragraphs:
            if keyword_lower in paragraph.lower():
                return _clip(paragraph, max_chars)
    return _clip(paragraphs[0], max_chars) if paragraphs else "No extracted text preview is available."


def _load_metadata(row: dict[str, Any]) -> dict[str, Any]:
    raw = row.get("structured_json")
    if isinstance(raw, dict):
        return raw
    if not raw:
        return {}
    try:
        loaded = json.loads(str(raw))
    except json.JSONDecodeError:
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _find_page_match(pages: object, keyword: object) -> dict[str, Any]:
    if not keyword or not isinstance(pages, list):
        return {}
    needle = str(keyword).strip().lower()
    if not needle:
        return {}
    for page in pages:
        if not isinstance(page, dict):
            continue
        text = str(page.get("text", ""))
        if needle in text.lower():
            return {
                "page": page.get("page"),
                "paragraph": _matching_paragraph(text, needle),
            }
    return {}


def highlight_keyword(text: str, keyword: str) -> str:
    if not keyword:
        return text
    pattern = re.compile(f"({re.escape(keyword)})", re.IGNORECASE)
    return pattern.sub(r"**\1**", text)


def _clip(text: str, max_chars: int) -> str:
    text = " ".join(text.split())
    if len(text) <= max_chars:
        return text
    return f"{text[: max_chars - 3]}..."
