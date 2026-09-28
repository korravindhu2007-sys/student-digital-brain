from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: int
    document_id: int
    source_filename: str
    page_number: int
    chunk_number: int
    text: str
    subject: str
    chapter: str
    estimated_topic: str
    character_count: int
    word_count: int
    section_heading: str = ""
    score: float = 0.0
    matched_keywords: tuple[str, ...] = ()

    def with_score(self, score: float, matched_keywords: tuple[str, ...]) -> "RetrievedChunk":
        return replace(self, score=score, matched_keywords=matched_keywords)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["matched_keywords"] = list(self.matched_keywords)
        payload["title"] = self.estimated_topic or self.chapter or self.source_filename
        return payload


class ChunkRetriever:
    """Load locally stored PDF chunks and their document metadata."""

    def __init__(self, db_path: Path | None = None) -> None:
        from neuronote.database import DatabaseManager
        self.manager = DatabaseManager(db_path)

    def chunks(self, document_ids: list[int] | None = None) -> list[RetrievedChunk]:
        documents = {int(doc["id"]): doc for doc in self.manager.list_documents()}
        wanted = set(document_ids or [])
        rows = self.manager.get_chunks()
        chunks: list[RetrievedChunk] = []
        for row in rows:
            document_id = int(row.get("document_id") or 0)
            if wanted and document_id not in wanted:
                continue
            document = documents.get(document_id, {})
            text = str(row.get("text", ""))
            subject = _coalesce(row.get("subject"), document.get("subject"), "General")
            chapter = _coalesce(row.get("chapter"), document.get("topic"), "General")
            estimated_topic = _coalesce(row.get("estimated_topic"), row.get("section_heading"), chapter)
            source = _coalesce(
                document.get("source_name"), document.get("filename"), document.get("title"), "unknown.pdf"
            )
            chunks.append(
                RetrievedChunk(
                    chunk_id=int(row.get("id") or 0),
                    document_id=document_id,
                    source_filename=source,
                    page_number=int(row.get("page_number") or row.get("page") or 1),
                    chunk_number=int(row.get("chunk_index") or 0),
                    text=text,
                    subject=subject,
                    chapter=chapter,
                    estimated_topic=estimated_topic,
                    character_count=int(row.get("character_count") or len(text)),
                    word_count=int(row.get("word_count") or len(text.split())),
                    section_heading=str(row.get("section_heading") or ""),
                )
            )
        return chunks


def _coalesce(*values: object) -> str:
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return ""
