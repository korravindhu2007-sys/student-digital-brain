"""Search service for NeuroNote."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from src.database.repository import search_chunks_fts
from neuronote.ollama import ollama_generate_json
from src.retrieval.retrieval_engine import RetrievalEngine
from src.services.cache_service import get_cache_service
from src.utils.logging import setup_logging

logger = setup_logging(__name__)


@dataclass
class SearchResult:
    """Search result structure."""
    query: str
    results: list[dict[str, Any]]
    total_found: int
    processing_time: float
    cache_hit: bool = False


class SearchService:
    """Service for semantic and keyword search."""

    def __init__(self, db_path: Optional[Any] = None) -> None:
        self.db_path = db_path
        self.retrieval_engine = RetrievalEngine(db_path)
        self.cache_service = get_cache_service()

    def semantic_search(self, query: str, document_ids: Optional[list[int]] = None,
                       top_k: int = 10) -> SearchResult:
        """Perform semantic search.

        Workflow:
            Normalize Query → Retrieve Chunks → Rank Results → Build Context → Ollama → Return

        Args:
            query: Search query.
            document_ids: Optional document filter.
            top_k: Maximum results.

        Returns:
            SearchResult with ranked results.
        """
        start_time = logger.info("Semantic search: %s", query[:100])

        try:
            # Check cache
            cache_key = f"search-semantic-{hash(query)}-{sorted(document_ids or [])}-{top_k}"
            cached = self.cache_service.lookup(cache_key, cache_type="search")
            if cached:
                logger.info("Cache hit for semantic search")
                return SearchResult(
                    query=query,
                    results=cached.get("results", []),
                    total_found=cached.get("total_found", 0),
                    processing_time=0,
                    cache_hit=True,
                )

            # Retrieve context
            retrieval_result = self.retrieval_engine.retrieve(
                query, document_ids=document_ids, top_k=top_k, purpose="search"
            )

            chunks = retrieval_result.get("chunks", [])
            context = retrieval_result.get("context", "")

            if not chunks:
                result = SearchResult(
                    query=query,
                    results=[],
                    total_found=0,
                    processing_time=0,
                )
                return result

            # Generate answer from context
            answer_data = self._generate_answer(query, context, chunks)

            # Build results
            results = []
            for idx, chunk in enumerate(chunks):
                results.append({
                    "text": chunk.get("text", ""),
                    "page": chunk.get("page_number") or chunk.get("page"),
                    "chunk_index": chunk.get("chunk_index"),
                    "relevance": 100 - (idx * 5),
                    "answer": answer_data.get("answer", "") if idx == 0 else "",
                    "definition": answer_data.get("definition", ""),
                    "explanation": answer_data.get("explanation", ""),
                    "example": answer_data.get("example", ""),
                })

            processing_time = (datetime.now() - start_time).total_seconds()
            result = SearchResult(
                query=query,
                results=results,
                total_found=len(results),
                processing_time=processing_time,
            )

            # Cache result
            cache_data = {
                "results": results,
                "total_found": len(results),
            }
            self.cache_service.store(cache_key, cache_data, cache_type="search",
                                   document_ids=document_ids)

            logger.info("Semantic search completed in %.2f seconds: %d results",
                       processing_time, len(results))
            return result

        except Exception as exc:
            logger.exception("Semantic search failed")
            return SearchResult(
                query=query,
                results=[],
                total_found=0,
                processing_time=0,
            )

    def search_definition(self, term: str, document_ids: Optional[list[int]] = None) -> SearchResult:
        """Search for definitions.

        Args:
            term: Term to define.
            document_ids: Optional document filter.

        Returns:
            SearchResult with definitions.
        """
        query = f"definition of {term}"
        result = self.semantic_search(query, document_ids=document_ids, top_k=5)

        # Enhance results with definition-specific data
        for res in result.results:
            res["search_type"] = "definition"

        return result

    def search_topic(self, topic: str, document_ids: Optional[list[int]] = None) -> SearchResult:
        """Search for topic information.

        Args:
            topic: Topic to search.
            document_ids: Optional document filter.

        Returns:
            SearchResult with topic info.
        """
        result = self.semantic_search(topic, document_ids=document_ids, top_k=10)

        for res in result.results:
            res["search_type"] = "topic"

        return result

    def search_example(self, concept: str, document_ids: Optional[list[int]] = None) -> SearchResult:
        """Search for examples.

        Args:
            concept: Concept to find examples for.
            document_ids: Optional document filter.

        Returns:
            SearchResult with examples.
        """
        query = f"example of {concept}"
        result = self.semantic_search(query, document_ids=document_ids, top_k=5)

        for res in result.results:
            res["search_type"] = "example"

        return result

    def search_formula(self, formula_name: str, document_ids: Optional[list[int]] = None) -> SearchResult:
        """Search for formulas.

        Args:
            formula_name: Formula to search.
            document_ids: Optional document filter.

        Returns:
            SearchResult with formulas.
        """
        query = f"formula {formula_name}"
        result = self.semantic_search(query, document_ids=document_ids, top_k=5)

        for res in result.results:
            res["search_type"] = "formula"

        return result

    def search_algorithm(self, algorithm_name: str, document_ids: Optional[list[int]] = None) -> SearchResult:
        """Search for algorithms.

        Args:
            algorithm_name: Algorithm to search.
            document_ids: Optional document filter.

        Returns:
            SearchResult with algorithms.
        """
        query = f"algorithm {algorithm_name}"
        result = self.semantic_search(query, document_ids=document_ids, top_k=5)

        for res in result.results:
            res["search_type"] = "algorithm"

        return result

    def search_hardware(self, hardware_name: str, document_ids: Optional[list[int]] = None) -> SearchResult:
        """Search for hardware information.

        Args:
            hardware_name: Hardware to search.
            document_ids: Optional document filter.

        Returns:
            SearchResult with hardware info.
        """
        query = f"hardware {hardware_name}"
        result = self.semantic_search(query, document_ids=document_ids, top_k=5)

        for res in result.results:
            res["search_type"] = "hardware"

        return result

    def search_software(self, software_name: str, document_ids: Optional[list[int]] = None) -> SearchResult:
        """Search for software information.

        Args:
            software_name: Software to search.
            document_ids: Optional document filter.

        Returns:
            SearchResult with software info.
        """
        query = f"software {software_name}"
        result = self.semantic_search(query, document_ids=document_ids, top_k=5)

        for res in result.results:
            res["search_type"] = "software"

        return result

    def _generate_answer(self, query: str, context: str, chunks: list[dict[str, Any]]) -> dict[str, Any]:
        """Generate structured answer from context."""
        try:
            from src.llm.ollama import ollama_generate

            prompt = f"""Based on the following context, answer the question.
Provide definition, explanation, and example if available.

Context:
{context}

Question: {query}

Provide a concise answer focusing on the key information."""

            answer_text = ollama_generate(prompt)

            return {
                "answer": answer_text,
                "definition": answer_text.split('.')[0] if answer_text else "",
                "explanation": answer_text,
                "example": "",
            }

        except Exception as exc:
            logger.error("Answer generation failed: %s", exc)
            return {
                "answer": chunks[0].get("text", "") if chunks else "",
                "definition": "",
                "explanation": "",
                "example": "",
            }


# Global service instance
_search_service: Optional[SearchService] = None


def get_search_service(db_path: Optional[Any] = None) -> SearchService:
    """Get or create search service instance."""
    global _search_service
    if _search_service is None or db_path:
        _search_service = SearchService(db_path)
    return _search_service