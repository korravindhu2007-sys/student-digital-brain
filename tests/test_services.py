"""Tests for services module."""


from src.services.quiz_service import QuizService
from src.services.revision_service import RevisionService


class TestQuizService:
    """Test quiz generation and management."""

    def setup_method(self):
        """Set up test fixtures."""
        self.quiz_service = QuizService()

    def test_validate_question_valid_mcq(self):
        """Test question validation for valid MCQ."""
        question = {
            "question": "What is 2+2?",
            "answer": "4",
            "type": "multiple_choice",
            "options": ["3", "4", "5", "6"],
        }
        assert self.quiz_service._validate_question(question) is True

    def test_validate_question_missing_fields(self):
        """Test question validation with missing fields."""
        question = {"question": "What is 2+2?"}
        assert self.quiz_service._validate_question(question) is False

    def test_normalize_question(self):
        """Test question normalization."""
        raw = {
            "question": "Test question?",
            "answer": "Answer",
            "type": "multiple_choice",
            "options": ["A", "B", "C", "D"],
            "difficulty": "hard",
            "explanation": "Because",
        }
        normalized = self.quiz_service._normalize_question(raw)
        assert normalized["question_text"] == "Test question?"
        assert normalized["answer"] == "Answer"
        assert normalized["difficulty"] == "hard"

    def test_shuffle_questions(self):
        """Test question shuffling."""
        questions = [
            {"question": "Q1", "answer": "A1"},
            {"question": "Q2", "answer": "A2"},
            {"question": "Q3", "answer": "A3"},
        ]
        shuffled = self.quiz_service.shuffle_questions(questions)
        assert len(shuffled) == len(questions)
        assert all(q in questions for q in shuffled)


class TestRevisionService:
    """Test revision planning."""

    def setup_method(self):
        """Set up test fixtures."""
        self.revision_service = RevisionService()

    def test_generate_revision_plan_empty_topics(self):
        """Test plan generation with no topics."""
        plan = self.revision_service.generate_revision_plan(subject_id=999, available_days=7)
        assert plan == []

    def test_mark_completed_invalid_session(self):
        """Test marking invalid session as completed."""
        result = self.revision_service.mark_completed(session_id=99999)
        assert result is False
