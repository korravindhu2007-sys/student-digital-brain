"""Chat service for NeuroNote."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from src.database.repository import (
    get_chat_history,
    save_chat_message,
)
from src.neuronote.ollama import ollama_generate_json as ollama_generate
from src.retrieval.retrieval_engine import RetrievalEngine
from src.services.cache_service import get_cache_service
from src.utils.logging import setup_logging

logger = setup_logging(__name__)


@dataclass
class ChatResponse:
    """Chat response structure."""
    answer: str
    sources: list[dict[str, Any]]
    confidence: int
    related_topics: list[str]
    suggested_followups: list[str]
    cache_hit: bool = False


class ChatService:
    """Service for AI-powered Q&A with document context."""

    def __init__(self, db_path: Optional[Any] = None) -> None:
        self.db_path = db_path
        self.retrieval_engine = RetrievalEngine(db_path)
        self.cache_service = get_cache_service()

    def ask(self, question: str, document_ids: Optional[list[int]] = None,
            session_id: str = "default") -> ChatResponse:
        """Ask a question and get AI-generated answer.

        Workflow:
            Question → Normalize → Retrieve Chunks → Build Context → Cache Check →
            Ollama → Store Chat → Return Answer

        Args:
            question: User question.
            document_ids: Optional document filter.
            session_id: Chat session ID.

        Returns:
            ChatResponse with answer and metadata.
        """
        start_time = logger.info("Processing question: %s", question[:100])

        try:
            # Normalize question
            normalized_question = question.strip()
            if not normalized_question:
                return ChatResponse(
                    answer="Please enter a question.",
                    sources=[],
                    confidence=0,
                    related_topics=[],
                    suggested_followups=[],
                )

            # Check cache
            cache_key = f"chat-{hash(normalized_question)}-{sorted(document_ids or [])}"
            cached = self.cache_service.lookup(cache_key, cache_type="chat")
            if cached:
                logger.info("Cache hit for question")
                return ChatResponse(
                    answer=cached.get("answer", ""),
                    sources=cached.get("sources", []),
                    confidence=cached.get("confidence", 0),
                    related_topics=cached.get("related_topics", []),
                    suggested_followups=cached.get("suggested_followups", []),
                    cache_hit=True,
                )

            # Retrieve relevant chunks
            retrieval_result = self.retrieval_engine.retrieve_for_chat(
                normalized_question, document_ids=document_ids
            )

            chunks = retrieval_result.get("chunks", [])
            context = retrieval_result.get("context", "")

            # Check if context available
            if not context or not chunks:
                response = ChatResponse(
                    answer="The uploaded document does not contain enough information to answer this question.",
                    sources=[],
                    confidence=0,
                    related_topics=[],
                    suggested_followups=[],
                )

                # Save user question
                self._save_message(session_id, document_ids[0] if document_ids else 0,
                                 "user", question, None, None, 0)
                # Save assistant response
                self._save_message(session_id, document_ids[0] if document_ids else 0,
                                 "assistant", response.answer, None, None, 0)

                return response

            # Generate response using Ollama
            ollama_response = self._call_ollama(normalized_question, context)

            # Parse response
            answer = ollama_response.get("answer", "")
            confidence = ollama_response.get("confidence", 85)
            related_topics = ollama_response.get("related_topics", [])
            suggested_followups = ollama_response.get("suggested_followups", [])

            # Build sources
            sources = retrieval_result.get("references", [])
            for idx, chunk in enumerate(chunks[:5]):
                sources.append({
                    "page": chunk.get("page_number") or chunk.get("page"),
                    "paragraph": chunk.get("chunk_index"),
                    "text": chunk.get("text", "")[:200],
                    "relevance": 100 - (idx * 10),
                })

            response = ChatResponse(
                answer=answer,
                sources=sources,
                confidence=confidence,
                related_topics=related_topics,
                suggested_followups=suggested_followups,
            )

            # Save to cache
            cache_data = {
                "answer": answer,
                "sources": sources,
                "confidence": confidence,
                "related_topics": related_topics,
                "suggested_followups": suggested_followups,
            }
            self.cache_service.store(cache_key, cache_data, cache_type="chat",
                                   document_ids=document_ids)

            # Save chat history
            self._save_message(session_id,
                             document_ids[0] if document_ids else 0,
                             "user", question, None, None, None)

            context_chunks = "; ".join([c.get("text", "")[:100] for c in chunks[:3]])
            self._save_message(session_id,
                             document_ids[0] if document_ids else 0,
                             "assistant", answer, context_chunks,
                             sources[0].get("page") if sources else None,
                             confidence)

            logger.info("Question answered in %.2f seconds", start_time)
            return response

        except Exception as exc:
            logger.exception("Chat failed")
            return ChatResponse(
                answer=f"An error occurred: {exc}",
                sources=[],
                confidence=0,
                related_topics=[],
                suggested_followups=[],
            )

    def answer(self, question: str, context: str) -> dict[str, Any]:
        """Generate answer from question and context.

        Args:
            question: User question.
            context: Retrieved context.

        Returns:
            Dict with answer and metadata.
        """
        return self._call_ollama(question, context)

    def build_context(self, chunks: list[dict[str, Any]], max_chars: int = 6000) -> str:
        """Build context from retrieved chunks.

        Args:
            chunks: Retrieved chunks.
            max_chars: Maximum context length.

        Returns:
            Formatted context string.
        """
        context_parts = []
        total_chars = 0

        for chunk in chunks:
            text = chunk.get("text", "")
            page = chunk.get("page_number") or chunk.get("page", "?")

            chunk_text = f"[Page {page}]\n{text}\n"
            if total_chars + len(chunk_text) > max_chars:
                break

            context_parts.append(chunk_text)
            total_chars += len(chunk_text)

        return "\n".join(context_parts)

    def retrieve_context(self, question: str, document_ids: Optional[list[int]] = None) -> dict[str, Any]:
        """Retrieve context for question.

        Args:
            question: User question.
            document_ids: Optional document filter.

        Returns:
            Retrieval result dict.
        """
        return self.retrieval_engine.retrieve_for_chat(question, document_ids=document_ids)

    def save_history(self, session_id: str, message: str, role: str = "user",
                    document_id: int = 0) -> int:
        """Save chat message to history.

        Args:
            session_id: Session ID.
            message: Message text.
            role: Message role ('user' or 'assistant').
            document_id: Related document ID.

        Returns:
            Message ID.
        """
        return self._save_message(session_id, document_id, role, message)

    def load_history(self, session_id: str, limit: int = 50) -> list[dict[str, Any]]:
        """Load chat history.

        Args:
            session_id: Session ID.
            limit: Maximum messages.

        Returns:
            List of message dicts.
        """
        return get_chat_history(session_id, limit=limit, db_path=self.db_path)

    def clear_history(self, session_id: str) -> bool:
        """Clear chat history.

        Args:
            session_id: Session ID.

        Returns:
            True if cleared.
        """
        try:
            from src.database.connection import get_db
            with get_db() as conn:
                conn.execute("DELETE FROM chat_history WHERE session_id = ?", (session_id,))
            logger.info("Cleared chat history for session %s", session_id)
            return True
        except Exception as exc:
            logger.error("Failed to clear history: %s", exc)
            return False

    def _call_ollama(self, question: str, context: str) -> dict[str, Any]:
        """Call Ollama to generate response."""
        try:
            prompt = f"""Answer the question using ONLY the provided context.
If the answer is not in the context, say "The uploaded document does not contain enough information to answer this question."

Context:
{context}

Question: {question}

Provide your response in the following JSON format:
{{
    "answer": "Your answer here",
    "confidence": 85,
    "related_topics": ["topic1", "topic2"],
    "suggested_followups": ["followup1", "followup2"]
}}

Remember: Answer ONLY from the context. Never invent facts."""

            response_text = ollama_generate(prompt)

            # Try to parse JSON from response
            try:
                import json
                import re
                # Extract JSON from response
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
            except Exception:
                pass

            # Fallback
            return {
                "answer": response_text,
                "confidence": 75,
                "related_topics": [],
                "suggested_followups": [],
            }

        except Exception as exc:
            logger.error("Ollama call failed: %s", exc)
            return {
                "answer": "The uploaded document does not contain enough information to answer this question.",
                "confidence": 0,
                "related_topics": [],
                "suggested_followups": [],
            }

    def _save_message(self, session_id: str, document_id: int, role: str,
                     message: str, context_chunks: Optional[str] = None,
                     source_page: Optional[int] = None,
                     confidence: Optional[float] = None) -> int:
        """Save chat message to database."""
        return save_chat_message(
            document_id=document_id,
            session_id=session_id,
            role=role,
            message=message,
            context_chunks=context_chunks,
            source_page=source_page,
            confidence=confidence,
            db_path=self.db_path,
        )


# Global service instance
_chat_service: Optional[ChatService] = None


def get_chat_service(db_path: Optional[Any] = None) -> ChatService:
    """Get or create chat service instance."""
    global _chat_service
    if _chat_service is None or db_path:
        _chat_service = ChatService(db_path)
    return _chat_service