from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .chunk_retriever import ChunkRetriever, RetrievedChunk
from .context_builder import ContextBuilder
from .ranking import RankingEngine
from .search_engine import normalize_query


class RetrievalEngine:
    """Retrieve relevant local chunks and build bounded context for Ollama."""

    def __init__(self, db_path: Path | None = None, *, max_context_chars: int = 6000) -> None:
        self.db_path = db_path
        self.retriever = ChunkRetriever(db_path)
        self.ranker = RankingEngine()
        self.context_builder = ContextBuilder(max_chars=max_context_chars)

    def retrieve(
        self,
        query: str,
        document_ids: list[int] | None = None,
        *,
        top_k: int = 5,
        purpose: str = "general",
        use_cache: bool = True,
    ) -> dict[str, Any]:
        from neuronote.database import get_search_cache, save_search_cache
        normalized = normalize_query(query, self._vocabulary(document_ids))
        query_hash = _cache_hash(purpose, normalized, document_ids, top_k)
        if use_cache:
            cached = get_search_cache(query_hash, db_path=self.db_path)
            if cached:
                cached["cache_hit"] = True
                return cached

        chunks = self.retriever.chunks(document_ids=document_ids)
        ranked = self.ranker.rank(normalized, chunks, top_k=top_k)
        context_payload = self.context_builder.build(ranked)
        response = {
            "query": query,
            "normalized_query": normalized,
            "purpose": purpose,
            "top_k": top_k,
            "chunks": [chunk.to_dict() for chunk in ranked],
            "context": context_payload["context"],
            "references": context_payload["references"],
            "cache_hit": False,
        }
        if use_cache:
            save_search_cache(query_hash, {"query": query, "document_ids": document_ids or []}, response, self.db_path)
        return response

    def retrieve_by_keyword(
        self, keyword: str, document_ids: list[int] | None = None, *, top_k: int = 5
    ) -> dict[str, Any]:
        return self.retrieve(keyword, document_ids=document_ids, top_k=top_k, purpose="keyword")

    def retrieve_by_topic(self, topic: str, document_ids: list[int] | None = None, *, top_k: int = 5) -> dict[str, Any]:
        return self.retrieve(topic, document_ids=document_ids, top_k=top_k, purpose="topic")

    def retrieve_by_subject(
        self, subject: str, document_ids: list[int] | None = None, *, top_k: int = 5
    ) -> dict[str, Any]:
        chunks = [
            chunk
            for chunk in self.retriever.chunks(document_ids=document_ids)
            if subject.lower() in chunk.subject.lower()
        ]
        ranked = self.ranker.rank(normalize_query(subject), chunks, top_k=top_k)
        context_payload = self.context_builder.build(ranked)
        return {
            "query": subject,
            "normalized_query": normalize_query(subject),
            "purpose": "subject",
            "top_k": top_k,
            "chunks": [chunk.to_dict() for chunk in ranked],
            "context": context_payload["context"],
            "references": context_payload["references"],
            "cache_hit": False,
        }

    def retrieve_for_chat(
        self, question: str, document_ids: list[int] | None = None, *, top_k: int = 5
    ) -> dict[str, Any]:
        return self.retrieve(question, document_ids=document_ids, top_k=top_k, purpose="chat")

    def retrieve_for_flashcards(
        self, query: str = "definition formula important concept", document_ids: list[int] | None = None
    ) -> dict[str, Any]:
        return self.retrieve(query, document_ids=document_ids, top_k=12, purpose="flashcards")

    def retrieve_for_study(
        self, query: str = "definition concept example algorithm formula", document_ids: list[int] | None = None
    ) -> dict[str, Any]:
        return self.retrieve(query, document_ids=document_ids, top_k=15, purpose="study")

    def retrieve_for_formula(
        self, query: str = "formula equation algorithm syntax", document_ids: list[int] | None = None
    ) -> dict[str, Any]:
        return self.retrieve(query, document_ids=document_ids, top_k=10, purpose="formula")

    def _vocabulary(self, document_ids: list[int] | None) -> set[str]:
        vocabulary: set[str] = set()
        for chunk in self.retriever.chunks(document_ids=document_ids):
            vocabulary.update(_chunk_words(chunk))
        return vocabulary


def _chunk_words(chunk: RetrievedChunk) -> set[str]:
    return set(normalize_query(" ".join([chunk.text, chunk.subject, chunk.chapter, chunk.estimated_topic])).split())


def _cache_hash(purpose: str, normalized_query: str, document_ids: list[int] | None, top_k: int) -> str:
    payload = {
        "purpose": purpose,
        "query": normalized_query,
        "document_ids": sorted(document_ids or []),
        "top_k": top_k,
        "version": 1,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
