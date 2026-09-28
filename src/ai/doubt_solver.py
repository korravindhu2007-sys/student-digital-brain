"""Doubt solver for NeuroNote - handles student questions naturally."""

from __future__ import annotations

from typing import Any

from src.ai.citation import CitationEngine
from src.ai.context_validator import ContextValidator
from src.ai.prompt_templates import get_doubt_solver_prompt
from src.ai.response_formatter import ResponseFormatter
from src.neuronote.ollama import ollama_generate
from src.retrieval.retrieval_engine import RetrievalEngine
from src.services.cache_service import get_cache_service
from src.utils.logging import setup_logging

logger = setup_logging(__name__)


class DoubtSolver:
    """Handles student doubts with natural language understanding.

    Workflow:
        Question → Normalize → Retrieve Chunks → Build Context →
        Validate Context → Call Ollama → Return Answer with Citations
    """

    def __init__(self, db_path: Any = None) -> None:
        self.db_path = db_path
        self.retrieval_engine = RetrievalEngine(db_path)
        self.cache_service = get_cache_service()
        self.validator = ContextValidator()
        self.formatter = ResponseFormatter()
        self.citation_engine = CitationEngine()

    def solve(self, question: str, document_ids: list[int] | None = None) -> dict[str, Any]:
        """Solve a student doubt using RAG pipeline.

        Args:
            question: Natural language question.
            document_ids: Optional document filter.

        Returns:
            Structured response dict with answer, citations, confidence.
        """
        logger.info("Solving doubt: %s", question[:100])

        try:
            # Step 1: Validate question
            cleaned = self.validator.validate_question(question)
            if cleaned is None:
                return self.formatter.format_no_answer_message("Please enter a valid question.")

            # Step 2: Check cache
            cache_key = f"doubt-{hash(cleaned)}-{sorted(document_ids or [])}"
            cached = self.cache_service.lookup(cache_key, cache_type="doubt")
            if cached:
                logger.info("Doubt cache hit")
                cached["cache_hit"] = True
                return cached

            # Step 3: Retrieve relevant chunks
            retrieval = self.retrieval_engine.retrieve_for_chat(cleaned, document_ids=document_ids)
            chunks = retrieval.get("chunks", [])
            context = retrieval.get("context", "")

            # Step 4: Validate context
            valid, error = self.validator.validate_all(cleaned, context, chunks)
            if not valid:
                response = self.formatter.format_no_answer_message(error)
                self.cache_service.store(cache_key, response, cache_type="doubt", document_ids=document_ids)
                return response

            # Step 5: Build prompt and call Ollama
            prompt = get_doubt_solver_prompt(context, cleaned)
            ollama_response = ollama_generate(prompt)

            # Step 6: Parse response
            parsed = self.formatter.parse_ollama_response(ollama_response)
            answer = parsed.get("answer", "")
            confidence = parsed.get("confidence", 75)
            related_topics = parsed.get("related_topics", [])
            followups = parsed.get(
                "suggested_followups",
                [
                    "Explain more",
                    "Give example",
                    "Real life example",
                    "Compare",
                    "Advantages",
                    "Disadvantages",
                    "Common mistakes",
                    "FAQ",
                ],
            )

            # Step 7: Build citations
            sources = self.citation_engine.build_citations(chunks)
            conf_score, conf_label = self.citation_engine.estimate_confidence(chunks)
            page_numbers = self.citation_engine.get_page_numbers(chunks)

            # Use the higher of the two confidence scores
            final_confidence = max(confidence, conf_score)

            # Step 8: Build response
            response = self.formatter.format_response(
                answer=answer,
                sources=sources,
                confidence=final_confidence,
                confidence_label=conf_label,
                related_topics=related_topics,
                followups=followups,
                page_numbers=page_numbers,
            )
            response["cache_hit"] = False

            # Step 9: Cache response
            self.cache_service.store(cache_key, response, cache_type="doubt", document_ids=document_ids)

            return response

        except Exception as exc:
            logger.exception("Doubt solver failed")
            return self.formatter.format_error_message(str(exc))
