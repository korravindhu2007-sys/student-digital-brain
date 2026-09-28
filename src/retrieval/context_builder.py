from __future__ import annotations

import re
from typing import Any

from .chunk_retriever import RetrievedChunk


class ContextBuilder:
    """Build bounded, page-cited context from ranked chunks."""

    def __init__(self, max_chars: int = 6000) -> None:
        self.max_chars = max_chars

    def build(self, chunks: list[RetrievedChunk]) -> dict[str, Any]:
        ordered = sorted(chunks, key=lambda item: (item.document_id, item.page_number, item.chunk_number))
        seen: set[str] = set()
        blocks: list[str] = []
        references: list[dict[str, Any]] = []
        used_chars = 0

        for chunk in ordered:
            text = _clean(chunk.text)
            fingerprint = _fingerprint(text)
            if not text or fingerprint in seen:
                continue
            header = f"Document: {chunk.source_filename}\nPage {chunk.page_number}\n"
            block = f"{header}{text}"
            projected = used_chars + len(block) + (2 if blocks else 0)
            if projected > self.max_chars:
                remaining = self.max_chars - used_chars - len(header) - (2 if blocks else 0)
                if remaining < 160:
                    break
                text = f"{text[: remaining - 3].rstrip()}..."
                block = f"{header}{text}"
            blocks.append(block)
            seen.add(fingerprint)
            used_chars += len(block) + (2 if len(blocks) > 1 else 0)
            references.append(
                {
                    "document_id": chunk.document_id,
                    "source_filename": chunk.source_filename,
                    "page_number": chunk.page_number,
                    "chunk_number": chunk.chunk_number,
                    "confidence": int(round(min(max(chunk.score, 0.0), 1.0) * 100)),
                    "matched_keywords": list(chunk.matched_keywords),
                }
            )
            if used_chars >= self.max_chars:
                break

        return {"context": "\n\n".join(blocks), "references": references}


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _fingerprint(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", text.lower())[:300]
