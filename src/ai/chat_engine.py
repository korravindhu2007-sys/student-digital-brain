"""Advanced Chat Engine for NeuroNote with full RAG pipeline."""

from __future__ import annotations

from typing import Any

from src.ai.citation import CitationEngine
from src.ai.context_validator import ContextValidator
from src.ai.conversation import ConversationManager
from src.ai.prompt_templates import get_chat_prompt
from src.ai.response_formatter import ResponseFormatter
from neuronote.ollama import ollama_generate_json as ollama_generate
from src.retrieval.retrieval_engine import RetrievalEngine
from src.services.cache_service import get_cache_service
from src.utils.logging import setup_logging

logger = setup_logging(__name__)


class ChatEngine:
    """Advanced RAG-powered chat engine.

    Pipeline:
        Question → Normalize → Intent Detection → Semantic Retrieval →
        Rank → Context Builder → Context Validator → Cache Check →
        Ollama (with intent-specific prompt) → Structured Response
    """

    def __init__(self, db_path: Any = None) -> None:
        self.db_path = db_path
        self.retrieval_engine = RetrievalEngine(db_path)
        self.cache_service = get_cache_service()
        self.validator = ContextValidator()
        self.formatter = ResponseFormatter()
        self.citation_engine = CitationEngine()
        self.conversation = ConversationManager(db_path)

    def ask(
        self,
        question: str,
        document_ids: list[int] | None = None,
        session_id: str = "default",
    ) -> dict[str, Any]:
        """Ask a question and get an AI-generated answer with full RAG.

        Args:
            question: User question.
            document_ids: Optional document filter.
            session_id: Chat session ID for conversation memory.

        Returns:
            Structured response with answer, citations, confidence, topics.
        """
        logger.info("ChatEngine.ask: %s (session=%s)", question[:80], session_id)

        try:
            # Step 1: Validate question
            cleaned = self.validator.validate_question(question)
            if cleaned is None:
                return self.formatter.format_no_answer_message("Please enter a valid question.")

            # Step 2: Check cache
            cache_key = f"chat-{hash(cleaned)}-{sorted(document_ids or [])}"
            cached = self.cache_service.lookup(cache_key, cache_type="chat")
            if cached:
                logger.info("Chat cache hit")
                cached["cache_hit"] = True
                return cached

            # Step 3: Retrieve relevant chunks (semantic search)
            retrieval = self.retrieval_engine.retrieve_for_chat(cleaned, document_ids=document_ids)
            chunks = retrieval.get("chunks", [])
            context = retrieval.get("context", "")

            # Step 4: Validate context before Ollama call
            valid, error = self.validator.validate_all(cleaned, context, chunks)
            if not valid:
                response = self.formatter.format_no_answer_message(error)
                self._save_conversation(session_id, document_ids, cleaned, response)
                self.cache_service.store(cache_key, response, cache_type="chat", document_ids=document_ids)
                return response

            # Step 5: Get conversation context for follow-up awareness
            conv_context = self.conversation.get_conversation_context(session_id, max_messages=4)
            full_context = context
            if conv_context:
                full_context = f"Previous conversation:\n{conv_context}\n\nCurrent context:\n{context}"

            # Step 6: Build intent-specific prompt and call Ollama
            prompt = get_chat_prompt(full_context, cleaned)
            ollama_response = ollama_generate(prompt)

            # Step 7: Parse Ollama response
            parsed = self.formatter.parse_ollama_response(ollama_response)
            answer = parsed.get("answer", "")
            confidence = parsed.get("confidence", 75)
            related_topics = parsed.get("related_topics", [])
            followups = parsed.get(
                "suggested_followups",
                [
                    "Explain more",
                    "Give example",
                    "Compare",
                    "Advantages",
                    "Disadvantages",
                    "Common mistakes",
                ],
            )

            # Step 8: Build citations
            sources = self.citation_engine.build_citations(chunks)
            conf_score, conf_label = self.citation_engine.estimate_confidence(chunks)
            page_numbers = self.citation_engine.get_page_numbers(chunks)

            # Use max confidence
            final_confidence = max(confidence, conf_score)

            # Step 9: Build final response
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

            # Step 10: Save conversation
            self._save_conversation(session_id, document_ids, cleaned, response)

            # Step 11: Cache response
            self.cache_service.store(cache_key, response, cache_type="chat", document_ids=document_ids)

            logger.info("Chat answered with confidence %d", final_confidence)
            return response

        except Exception as exc:
            logger.exception("Chat engine failed")
            return self.formatter.format_error_message(str(exc))

    def _save_conversation(
        self,
        session_id: str,
        document_ids: list[int] | None,
        question: str,
        response: dict[str, Any],
    ) -> None:
        """Save conversation to database.

        Args:
            session_id: Session ID.
            document_ids: Document IDs.
            question: User question.
            response: AI response.
        """
        doc_id = document_ids[0] if document_ids else 0
        try:
            self.conversation.save_message(
                session_id=session_id,
                document_id=doc_id,
                role="user",
                message=question,
            )
            self.conversation.save_message(
                session_id=session_id,
                document_id=doc_id,
                role="assistant",
                message=response.get("answer", ""),
                source_page=response.get("source_pages", [None])[0] if response.get("source_pages") else None,
                confidence=float(response.get("confidence", 0)),
            )
        except Exception as exc:
            logger.warning("Failed to save conversation: %s", exc)

    def get_history(self, session_id: str, limit: int = 50) -> list[dict[str, Any]]:
        """Get chat history for a session.

        Args:
            session_id: Session ID.
            limit: Max messages.

        Returns:
            List of messages.
        """
        return self.conversation.load_history(session_id, limit=limit)

    def clear_history(self, session_id: str) -> bool:
        """Clear chat history for a session.

        Args:
            session_id: Session ID.

        Returns:
            True if cleared.
        """
        return self.conversation.clear_session(session_id)

    def get_sessions(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent chat sessions.

        Args:
            limit: Max sessions.

        Returns:
            List of session summaries.
        """
        return self.conversation.get_recent_sessions(limit=limit)
