"""Study material generation service for NeuroNote."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

from src.database.repository import get_study_notes, save_study_notes
from src.llm.engine import LLMEngine as LLMService
from src.retrieval.retrieval_engine import RetrievalEngine
from src.services.cache_service import get_cache_service
from src.utils.logging import setup_logging

logger = setup_logging(__name__)


@dataclass
class StudyNotes:
    """Study notes structure."""
    introduction: str
    definitions: list[str]
    core_concepts: list[str]
    examples: list[str]
    applications: list[str]
    summary: str
    subject: str
    topic: str


class StudyService:
    """Service for generating structured study materials."""

    def __init__(self, db_path: Optional[Any] = None) -> None:
        self.db_path = db_path
        self.llm_service = LLMService()
        self.retrieval_engine = RetrievalEngine(db_path)
        self.cache_service = get_cache_service()

    def generate_study_notes(self, document_id: int, metadata: Optional[dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate structured study notes for a document.

        Args:
            document_id: Document ID.
            metadata: Optional metadata.

        Returns:
            Dict with study notes sections.
        """
        start_time = logger.info("Generating study notes for document %d", document_id)

        try:
            # Check cache
            cache_key = f"study-{document_id}"
            cached = self.cache_service.lookup(cache_key, cache_type="study")
            if cached:
                logger.info("Cache hit for study notes")
                return cached

            # Retrieve context
            retrieval_result = self.retrieval_engine.retrieve_for_study(document_ids=[document_id])
            context = retrieval_result.get("context", "")
            chunks = retrieval_result.get("chunks", [])

            if not context:
                return {
                    "introduction": "No content available.",
                    "definitions": [],
                    "core_concepts": [],
                    "examples": [],
                    "applications": [],
                    "summary": "No content available.",
                    "subject": "General",
                    "topic": "General",
                }

            # Generate study notes using LLM
            study_data = self._generate_from_llm(context, metadata)

            # Save to database
            self._save_to_database(document_id, study_data)

            execution_time = (datetime.now() - start_time).total_seconds()
            logger.info("Study notes generated in %.2f seconds", execution_time)

            # Cache result
            self.cache_service.store(cache_key, study_data, cache_type="study",
                                   document_ids=[document_id])

            return study_data

        except Exception as exc:
            logger.exception("Study notes generation failed")
            return self._fallback_study_notes(metadata)

    def extract_definitions(self, text: str) -> list[dict[str, str]]:
        """Extract definitions from text.

        Args:
            text: Source text.

        Returns:
            List of definition dicts.
        """
        return self.llm_service.extract_definitions(text)

    def extract_concepts(self, text: str) -> list[dict[str, Any]]:
        """Extract core concepts from text.

        Args:
            text: Source text.

        Returns:
            List of concept dicts.
        """
        return self.llm_service.extract_concepts(text)

    def extract_examples(self, text: str) -> list[str]:
        """Extract examples from text.

        Args:
            text: Source text.

        Returns:
            List of example strings.
        """
        return self.llm_service.extract_examples(text)

    def extract_applications(self, text: str) -> list[str]:
        """Extract applications from text.

        Args:
            text: Source text.

        Returns:
            List of application strings.
        """
        return self.llm_service.extract_applications(text)

    def extract_algorithms(self, text: str) -> list[dict[str, str]]:
        """Extract algorithms from text.

        Args:
            text: Source text.

        Returns:
            List of algorithm dicts.
        """
        return self.llm_service.extract_algorithms(text)

    def extract_hardware(self, text: str) -> list[dict[str, str]]:
        """Extract hardware information from text.

        Args:
            text: Source text.

        Returns:
            List of hardware dicts.
        """
        return self.llm_service.extract_hardware(text)

    def extract_software(self, text: str) -> list[dict[str, str]]:
        """Extract software information from text.

        Args:
            text: Source text.

        Returns:
            List of software dicts.
        """
        return self.llm_service.extract_software(text)

    def extract_summary(self, text: str) -> str:
        """Extract summary from text.

        Args:
            text: Source text.

        Returns:
            Summary string.
        """
        return self.llm_service.extract_summary(text)

    def _generate_from_llm(self, context: str, metadata: Optional[dict[str, Any]]) -> Dict[str, Any]:
        """Generate study notes using LLM."""
        try:
            from src.llm.ollama import ollama_generate_json
            from src.prompts import study_notes_prompt

            prompt = study_notes_prompt(context, metadata)
            result = ollama_generate_json(prompt)

            if result and isinstance(result, dict):
                return {
                    "introduction": result.get("introduction", ""),
                    "definitions": result.get("definitions", []),
                    "core_concepts": result.get("concepts", result.get("core_concepts", [])),
                    "examples": result.get("examples", []),
                    "applications": result.get("applications", []),
                    "summary": result.get("summary", ""),
                    "subject": metadata.get("subject", "General") if metadata else "General",
                    "topic": metadata.get("topic", "General") if metadata else "General",
                }

        except Exception as exc:
            logger.warning("LLM study notes generation failed: %s", exc)

        return self._fallback_study_notes(metadata)

    def _fallback_study_notes(self, metadata: Optional[dict[str, Any]]) -> Dict[str, Any]:
        """Fallback study notes without LLM."""
        subject = metadata.get("subject", "General") if metadata else "General"
        topic = metadata.get("topic", "General") if metadata else "General"

        return {
            "introduction": f"Study notes for {subject} - {topic}.",
            "definitions": [],
            "core_concepts": [],
            "examples": [],
            "applications": [],
            "summary": "No content available to generate study notes.",
            "subject": subject,
            "topic": topic,
        }

    def _save_to_database(self, document_id: int, study_data: Dict[str, Any]) -> None:
        """Save study notes to database."""
        notes_dict = {
            "Introduction": study_data.get("introduction", ""),
            "Definitions": "\n".join(study_data.get("definitions", [])),
            "Core_Concepts": "\n".join(str(c) for c in study_data.get("core_concepts", [])),
            "Examples": "\n".join(study_data.get("examples", [])),
            "Applications": "\n".join(study_data.get("applications", [])),
            "Summary": study_data.get("summary", ""),
        }

        save_study_notes(document_id, notes_dict, db_path=self.db_path)
        logger.info("Saved study notes for document %d", document_id)


# Global service instance
_study_service: Optional[StudyService] = None


def get_study_service(db_path: Optional[Any] = None) -> StudyService:
    """Get or create study service instance."""
    global _study_service
    if _study_service is None or db_path:
        _study_service = StudyService(db_path)
    return _study_service