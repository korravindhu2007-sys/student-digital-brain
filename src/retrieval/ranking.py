from __future__ import annotations

import difflib
import re

from .chunk_retriever import RetrievedChunk


class RankingEngine:
    """Rank chunks using lexical, sentence, topic, page, and frequency signals."""

    def rank(
        self,
        query: str,
        chunks: list[RetrievedChunk],
        *,
        top_k: int = 5,
        preferred_page: int | None = None,
    ) -> list[RetrievedChunk]:
        terms = _terms(query)
        if not terms:
            return []
        ranked: list[RetrievedChunk] = []
        for chunk in chunks:
            score, matched = self._score_chunk(terms, chunk, preferred_page)
            if score > 0:
                ranked.append(chunk.with_score(round(score, 4), tuple(matched)))
        ranked.sort(key=lambda item: (-item.score, item.document_id, item.page_number, item.chunk_number))
        return ranked[:top_k]

    def _score_chunk(
        self,
        terms: list[str],
        chunk: RetrievedChunk,
        preferred_page: int | None,
    ) -> tuple[float, list[str]]:
        text = chunk.text.lower()
        words = re.findall(r"[a-z0-9]+", text)
        matched: list[str] = []
        frequency = 0

        for term in terms:
            exact_count = text.count(term)
            fuzzy_count = 0
            if exact_count == 0 and len(term) >= 5:
                fuzzy_count = len(difflib.get_close_matches(term, words, n=3, cutoff=0.84))
            if exact_count or fuzzy_count:
                matched.append(term)
                frequency += exact_count + fuzzy_count

        if not matched:
            return 0.0, []

        keyword_similarity = len(set(matched)) / max(len(set(terms)), 1)
        sentence_similarity = _best_sentence_overlap(terms, chunk.text)
        topic_text = " ".join([chunk.subject, chunk.chapter, chunk.estimated_topic, chunk.section_heading]).lower()
        topic_similarity = sum(1 for term in terms if term in topic_text) / max(len(set(terms)), 1)
        frequency_score = min(frequency / 8.0, 1.0)
        page_score = 0.0
        if preferred_page is not None:
            distance = abs(chunk.page_number - preferred_page)
            page_score = max(0.0, 1.0 - min(distance, 10) / 10.0)

        score = (
            keyword_similarity * 0.45
            + sentence_similarity * 0.25
            + topic_similarity * 0.15
            + frequency_score * 0.10
            + page_score * 0.05
        )
        return score, sorted(set(matched))


def _terms(query: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", query.lower())


def _best_sentence_overlap(terms: list[str], text: str) -> float:
    wanted = set(terms)
    if not wanted:
        return 0.0
    best = 0.0
    for sentence in re.split(r"(?<=[.!?])\s+", text):
        sentence_terms = set(_terms(sentence))
        if not sentence_terms:
            continue
        best = max(best, len(wanted & sentence_terms) / len(wanted))
    return best
