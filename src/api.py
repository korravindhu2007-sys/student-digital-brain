"""Public API facade for NeuroNote backend.

This module provides a clean, unified interface for the frontend
to interact with all backend services without needing to know
the internal module structure.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from src.database.repository import get_all_subjects, get_document_stats
from src.graph.builder import KnowledgeGraphBuilder
from src.search.engine import SearchEngine
from src.services.processor import DocumentProcessor
from src.services.quiz_service import QuizService
from src.services.revision_service import RevisionService
from src.utils.file_utils import ensure_directories, validate_file
from src.utils.logging import setup_logging

logger = setup_logging(__name__)


class NeuroNoteAPI:
    """Unified API for NeuroNote backend services.

    All frontend interactions should go through this class.
    """

    def __init__(self) -> None:
        self.processor = DocumentProcessor()
        self.quiz_service = QuizService()
        self.revision_service = RevisionService()
        self.search_engine = SearchEngine()
        self.graph_builder = KnowledgeGraphBuilder()

    def initialize(self) -> Dict[str, Any]:
        """Initialize the application.

        Creates directories, initializes database, and loads models.

        Returns:
            Status dict with initialization results.
        """
        try:
            ensure_directories()

            from src.database.schema import initialize_database

            initialize_database()

            logger.info("NeuroNote API initialized successfully")
            return {"status": "success", "message": "Application initialized"}
        except Exception as e:
            logger.error("Initialization failed: %s", e)
            return {"status": "error", "message": str(e)}

    # ──────────────────────────────────────────────
    # Document Processing
    # ──────────────────────────────────────────────

    def process_document(self, file_path: str, subject_name: str = "General") -> Dict[str, Any]:
        """Process a document file (PDF, text, etc.).

        Args:
            file_path: Path to the document.
            subject_name: Subject to associate with.

        Returns:
            Processing result.
        """
        return self.upload_and_process(file_path, subject_name)

    def process_image(
        self, file_path: str, subject_name: str = "General", image_type: str = "printed"
    ) -> Dict[str, Any]:
        """Process an image file with OCR.

        Args:
            file_path: Path to the image.
            subject_name: Subject to associate with.
            image_type: Type of image ('printed', 'handwritten', 'whiteboard').

        Returns:
            Processing result with extracted text and concepts.
        """
        return self.upload_and_process(
            file_path,
            subject_name,
            metadata={"image_type": image_type},
        )

    def process_audio(self, file_path: str, subject_name: str = "General") -> Dict[str, Any]:
        """Process an audio file with speech-to-text.

        Args:
            file_path: Path to the audio file.
            subject_name: Subject to associate with.

        Returns:
            Processing result with transcript and concepts.
        """
        return self.upload_and_process(file_path, subject_name)

    def extract_text(self, file_path: str) -> str:
        """Extract raw text from a file without full processing.

        Args:
            file_path: Path to the file.

        Returns:
            Extracted text string.
        """
        from pathlib import Path

        from src.ingestion.pdf_extractor import PDFExtractor
        from src.ocr.processor import OCRProcessor
        from src.speech.transcriber import WhisperTranscriber

        file_path_obj = Path(file_path)
        file_type, _ = validate_file(file_path_obj)

        if file_type == "pdf":
            extractor = PDFExtractor(file_path_obj)
            return extractor.extract_all_text()
        elif file_type == "image":
            ocr = OCRProcessor()
            return ocr.extract_text(file_path_obj)
        elif file_type == "audio":
            transcriber = WhisperTranscriber()
            result = transcriber.transcribe(file_path_obj)
            return result.get("text", "")
        elif file_type == "text":
            with open(file_path_obj, "r", encoding="utf-8") as f:
                return f.read()
        return ""

    def extract_topics(self, text: str) -> List[Dict[str, Any]]:
        """Extract topics from text using LLM.

        Args:
            text: Text to analyze.

        Returns:
            List of topic dicts.
        """
        from src.llm.engine import LLMEngine
        from src.parser.json_parser import JSONParser

        llm = LLMEngine()
        parser = JSONParser()

        prompt = f"""Analyze the following text and identify the main topics covered.

Text:
{text[:2000]}  # Limit to first 2000 chars for efficiency

Respond with JSON:
{{
  "topics": [
    {{
      "name": "Topic Name",
      "description": "Brief description",
      "relevance": "high/medium/low"
    }}
  ]
}}"""

        try:
            raw_json = llm.extract_json(prompt=prompt)
            parsed = parser.parse_raw_json(raw_json)
            if parsed and "topics" in parsed:
                return parsed["topics"]
        except Exception as e:
            logger.error("Topic extraction failed: %s", e)

        return []

    def generate_structured_json(self, text: str, subject: str = "General") -> Dict[str, Any]:
        """Generate structured JSON from text.

        Args:
            text: Input text.
            subject: Subject name.

        Returns:
            Structured JSON with concepts, topics, etc.
        """
        from src.llm.engine import LLMEngine
        from src.parser.json_parser import JSONParser

        llm = LLMEngine()
        parser = JSONParser()

        prompt = f"""Analyze the following educational text and extract structured knowledge.

Subject: {subject}

Text:
{text[:3000]}

Extract and respond with JSON:
{{
  "subject": "{subject}",
  "summary": "Brief summary of the content",
  "keywords": ["keyword1", "keyword2"],
  "concepts": [
    {{
      "term": "Concept Name",
      "definition": "Clear definition",
      "importance": "high/medium/low"
    }}
  ],
  "topics": ["Topic 1", "Topic 2"],
  "important_questions": ["Question 1?", "Question 2?"]
}}"""

        try:
            raw_json = llm.extract_json(prompt=prompt)
            parsed = parser.parse_raw_json(raw_json)
            if parsed:
                parsed["source_document"] = "extracted_text"
                parsed["created_at"] = str(datetime.now())
                return parsed
        except Exception as e:
            logger.error("Structured JSON generation failed: %s", e)

        return {
            "subject": subject,
            "summary": "",
            "keywords": [],
            "concepts": [],
            "topics": [],
            "important_questions": [],
        }

    def save_document(
        self, title: str, file_type: str, file_path: str, subject_name: str = "General"
    ) -> int:
        """Save a document record to database.

        Args:
            title: Document title.
            file_type: File type.
            file_path: Path to file.
            subject_name: Subject name.

        Returns:
            Document ID.
        """
        from pathlib import Path

        from src.database.repository import create_document, get_or_create_subject

        subject_id = get_or_create_subject(subject_name)
        file_path_obj = Path(file_path)
        file_size = file_path_obj.stat().st_size if file_path_obj.exists() else 0

        return create_document(
            title=title,
            file_type=file_type,
            file_path=file_path,
            file_size=file_size,
            subject_id=subject_id,
        )

    def build_knowledge_graph(self, subject_id: Optional[int] = None) -> Dict[str, Any]:
        """Build knowledge graph from database.

        Args:
            subject_id: Optional subject filter.

        Returns:
            Graph data with nodes and edges.
        """
        return self.get_knowledge_graph(subject_id)

    def search_topics(
        self, query: str, subject_id: Optional[int] = None, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Search for topics.

        Args:
            query: Search query.
            subject_id: Optional subject filter.
            limit: Maximum results.

        Returns:
            List of topic dicts.
        """
        from src.database.connection import get_db

        pattern = f"%{query}%"
        sql = "SELECT * FROM topics WHERE name LIKE ?"
        params: List[Any] = [pattern]

        if subject_id is not None:
            sql += " AND subject_id = ?"
            params.append(subject_id)

        sql += " LIMIT ?"
        params.append(limit)

        with get_db() as conn:
            cursor = conn.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]

    def search_subject(self, subject_name: str) -> Optional[Dict[str, Any]]:
        """Search for a subject by name.

        Args:
            subject_name: Subject name to search for.

        Returns:
            Subject dict or None.
        """
        from src.database.connection import get_db

        with get_db() as conn:
            cursor = conn.execute("SELECT * FROM subjects WHERE name = ?", (subject_name,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def search_keyword(
        self, keyword: str, search_type: str = "all", limit: int = 20
    ) -> Dict[str, Any]:
        """Search by keyword across all content.

        Args:
            keyword: Keyword to search for.
            search_type: Type of search ('all', 'definitions', 'documents').
            limit: Maximum results.

        Returns:
            Search results.
        """
        return self.search(query=keyword, search_type=search_type, limit=limit)

    def upload_and_process(
        self,
        file_path: str,
        subject_name: str = "General",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Upload and process a document.

        Args:
            file_path: Path to the uploaded file.
            subject_name: Subject to associate with.
            metadata: Optional metadata (image_type, etc.).

        Returns:
            Processing result with document_id and status.
        """
        from pathlib import Path

        file_path_obj = Path(file_path)
        return self.processor.process_file(
            file_path=file_path_obj,
            subject_name=subject_name,
            metadata=metadata,
        )

    def search(
        self,
        query: str,
        search_type: str = "all",
        subject_id: Optional[int] = None,
        file_type: Optional[str] = None,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """Search across all knowledge.

        Args:
            query: Search query string.
            search_type: 'all', 'documents', 'definitions', or 'questions'.
            subject_id: Optional subject filter.
            file_type: Optional file type filter.
            limit: Maximum results.

        Returns:
            Search results with 'results' and 'total'.
        """
        return self.search_engine.search(
            query=query,
            search_type=search_type,
            subject_id=subject_id,
            file_type=file_type,
            limit=limit,
        )

    def get_suggestions(self, prefix: str, limit: int = 10) -> List[str]:
        """Get autocomplete suggestions.

        Args:
            prefix: Search prefix.
            limit: Maximum suggestions.

        Returns:
            List of suggestion strings.
        """
        return self.search_engine.get_suggestions(prefix, limit)

    def generate_quiz(
        self,
        subject_id: int,
        topic_id: Optional[int] = None,
        count: int = 10,
        difficulty: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Generate quiz questions.

        Args:
            subject_id: Subject ID.
            topic_id: Optional topic filter.
            count: Number of questions.
            difficulty: Optional difficulty.

        Returns:
            List of question dicts.
        """
        return self.quiz_service.generate_questions(
            subject_id=subject_id,
            topic_id=topic_id,
            count=count,
            difficulty=difficulty,
        )

    def submit_quiz(
        self,
        subject_id: int,
        questions: List[Dict[str, Any]],
        answers: List[str],
        topic_id: Optional[int] = None,
        duration_seconds: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Submit a completed quiz.

        Args:
            subject_id: Subject ID.
            questions: List of question dicts.
            answers: List of user answers.
            topic_id: Optional topic ID.
            duration_seconds: Time taken.

        Returns:
            Score and results.
        """
        return self.quiz_service.submit_quiz(
            subject_id=subject_id,
            topic_id=topic_id,
            questions=questions,
            answers=answers,
            duration_seconds=duration_seconds,
        )

    def create_revision_plan(
        self,
        subject_id: int,
        available_days: int,
        hours_per_day: float = 2.0,
    ) -> List[Dict[str, Any]]:
        """Create a revision plan.

        Args:
            subject_id: Subject ID.
            available_days: Days until exam.
            hours_per_day: Study hours per day.

        Returns:
            List of revision sessions.
        """
        return self.revision_service.generate_revision_plan(
            subject_id=subject_id,
            available_days=available_days,
            hours_per_day=hours_per_day,
        )

    def get_knowledge_graph(self, subject_id: Optional[int] = None) -> Dict[str, Any]:
        """Get knowledge graph data for visualization.

        Args:
            subject_id: Optional subject filter.

        Returns:
            Dict with 'nodes' and 'edges' lists.
        """
        from src.database.repository import (
            get_knowledge_graph_edges,
            search_definitions,
        )

        definitions = search_definitions(query="", subject_id=subject_id, limit=1000)
        edges = get_knowledge_graph_edges(subject_id=subject_id, limit=500)

        return self.graph_builder.build_from_database(definitions, edges)

    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get dashboard statistics.

        Returns:
            Dict with document counts, subject counts, etc.
        """
        doc_stats = get_document_stats()
        subjects = get_all_subjects()

        return {
            "documents": doc_stats,
            "subjects": len(subjects),
            "subject_list": subjects,
        }

    def get_subjects(self) -> List[Dict[str, Any]]:
        """Get all subjects.

        Returns:
            List of subject dicts.
        """
        return get_all_subjects()


# Global singleton API instance
api = NeuroNoteAPI()
