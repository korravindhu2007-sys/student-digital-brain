from __future__ import annotations

import difflib
import re
from pathlib import Path
from typing import Any

from .chunk_retriever import ChunkRetriever, RetrievedChunk
from .ranking import RankingEngine

STOP_WORDS = {
    "what",
    "is",
    "the",
    "a",
    "an",
    "please",
    "tell",
    "about",
    "explain",
    "give",
    "example",
    "examples",
    "etc",
    "of",
    "to",
    "me",
}

FUZZY_ALIASES = {
    "normalisation": "normalization",
    "algoritham": "algorithm",
    "databse": "database",
}


def normalize_query(query: str, vocabulary: set[str] | None = None) -> str:
    lowered = query.lower()
    lowered = re.sub(r"[^a-z0-9\s-]", " ", lowered)
    terms = [term for term in re.split(r"[\s-]+", lowered) if term and term not in STOP_WORDS]
    normalized: list[str] = []
    vocabulary = vocabulary or set()
    for term in terms:
        candidate = FUZZY_ALIASES.get(term, term)
        if vocabulary and candidate not in vocabulary and len(candidate) >= 5:
            matches = difflib.get_close_matches(candidate, vocabulary, n=1, cutoff=0.84)
            if matches:
                candidate = matches[0]
        normalized.append(candidate)
    return " ".join(normalized)


class SemanticSearch:
    """Search local SQLite chunks and return source-rich results."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.retriever = ChunkRetriever(db_path)
        self.ranker = RankingEngine()

    def search(
        self,
        query: str,
        document_ids: list[int] | None = None,
        *,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        chunks = self.retriever.chunks(document_ids=document_ids)
        normalized = normalize_query(query, _vocabulary(chunks))
        ranked = self.ranker.rank(normalized, chunks, top_k=top_k)
        return [self._format_result(chunk) for chunk in ranked]

    def search_topic(self, topic: str, document_ids: list[int] | None = None) -> list[dict[str, Any]]:
        return self.search(topic, document_ids=document_ids)

    def search_definition(self, query: str, document_ids: list[int] | None = None) -> list[dict[str, Any]]:
        return self.search(f"definition {query}", document_ids=document_ids)

    def search_formula(self, query: str, document_ids: list[int] | None = None) -> list[dict[str, Any]]:
        return self.search(f"formula equation {query}", document_ids=document_ids)

    def search_algorithm(self, query: str, document_ids: list[int] | None = None) -> list[dict[str, Any]]:
        return self.search(f"algorithm steps {query}", document_ids=document_ids)

    def search_examples(self, query: str, document_ids: list[int] | None = None) -> list[dict[str, Any]]:
        return self.search(f"example {query}", document_ids=document_ids)

    def search_hardware(self, query: str, document_ids: list[int] | None = None) -> list[dict[str, Any]]:
        return self.search(f"hardware {query}", document_ids=document_ids)

    def search_software(self, query: str, document_ids: list[int] | None = None) -> list[dict[str, Any]]:
        return self.search(f"software {query}", document_ids=document_ids)

    def _format_result(self, chunk: RetrievedChunk) -> dict[str, Any]:
        return {
            "title": chunk.estimated_topic or chunk.chapter or chunk.source_filename,
            "page_number": chunk.page_number,
            "paragraph": chunk.text,
            "confidence": int(round(min(max(chunk.score, 0.0), 1.0) * 100)),
            "matched_keywords": list(chunk.matched_keywords),
            "source_filename": chunk.source_filename,
            "document_id": chunk.document_id,
            "chunk_number": chunk.chunk_number,
        }


def _vocabulary(chunks: list[RetrievedChunk]) -> set[str]:
    words: set[str] = set()
    for chunk in chunks:
        words.update(re.findall(r"[a-z0-9]+", chunk.text.lower()))
        words.update(re.findall(r"[a-z0-9]+", chunk.subject.lower()))
        words.update(re.findall(r"[a-z0-9]+", chunk.chapter.lower()))
        words.update(re.findall(r"[a-z0-9]+", chunk.estimated_topic.lower()))
    return words
