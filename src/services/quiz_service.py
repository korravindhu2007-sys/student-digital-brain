"""Quiz generation and management service for NeuroNote."""

import random
from typing import Any, Dict, List, Optional

from src.database.repository import (
    get_questions_for_quiz,
    save_quiz_result,
)
from src.llm.engine import LLMEngine
from src.utils.logging import setup_logging

logger = setup_logging(__name__)


class QuizService:
    """Generate and manage quizzes from the knowledge base."""

    def __init__(self) -> None:
        self.llm_engine = LLMEngine()

    def generate_questions(
        self,
        subject_id: int,
        topic_id: Optional[int] = None,
        count: int = 10,
        difficulty: Optional[str] = None,
        use_llm: bool = True,
    ) -> List[Dict[str, Any]]:
        """Generate quiz questions for a subject/topic.

        Args:
            subject_id: Subject ID.
            topic_id: Optional topic filter.
            count: Number of questions to generate.
            difficulty: Optional difficulty filter.
            use_llm: Whether to use LLM for generation (vs database).

        Returns:
            List of question dicts.
        """
        if use_llm:
            return self._generate_with_llm(subject_id, topic_id, count, difficulty)
        else:
            return get_questions_for_quiz(
                subject_id=subject_id,
                topic_id=topic_id,
                count=count,
                difficulty=difficulty,
            )

    def _generate_with_llm(
        self,
        subject_id: int,
        topic_id: Optional[int],
        count: int,
        difficulty: Optional[str],
    ) -> List[Dict[str, Any]]:
        """Generate questions using the LLM.

        Args:
            subject_id: Subject ID.
            topic_id: Optional topic.
            count: Number of questions.
            difficulty: Optional difficulty.

        Returns:
            List of question dicts.
        """
        # Get context from existing definitions
        from src.database.repository import search_definitions

        definitions = search_definitions(
            query="",
            subject_id=subject_id,
            limit=20,
        )

        if not definitions:
            logger.warning("No definitions found for subject %d", subject_id)
            return []

        # Build context text
        context_text = "\n".join(f"- {d['term']}: {d['definition']}" for d in definitions[:15])

        prompt = f"""Generate {count} quiz questions based on the following concepts.

Concepts:
{context_text}

Requirements:
- Mix of multiple_choice (4 options), true_false, and short_answer questions
- Difficulty: {difficulty or "medium"}
- Ensure questions test understanding, not just memorization
- Include the correct answer and a brief explanation

Respond with JSON array:
[
  {{
    "question": "Question text here?",
    "answer": "Correct answer",
    "options": ["A", "B", "C", "D"],
    "type": "multiple_choice",
    "difficulty": "medium",
    "explanation": "Why this is correct"
  }}
]"""

        system_prompt = (
            "You are an expert educator creating quiz questions. "
            "Generate clear, accurate, and pedagogically sound questions. "
            "Always respond with valid JSON."
        )

        try:
            raw_json = self.llm_engine.extract_json(
                prompt=prompt,
                system_prompt=system_prompt,
            )
            questions = raw_json if isinstance(raw_json, list) else raw_json.get("questions", [])

            # Validate and normalize
            valid_questions = []
            for q in questions[:count]:
                if self._validate_question(q):
                    valid_questions.append(self._normalize_question(q))

            logger.info("Generated %d questions via LLM", len(valid_questions))
            return valid_questions

        except Exception as e:
            logger.error("LLM question generation failed: %s", e)
            return []

    def _validate_question(self, question: Dict[str, Any]) -> bool:
        """Validate a question has required fields.

        Args:
            question: Question dict.

        Returns:
            True if valid.
        """
        required = ["question", "answer", "type"]
        return all(field in question for field in required)

    def _normalize_question(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize question to standard format.

        Args:
            question: Raw question dict.

        Returns:
            Normalized question dict.
        """
        return {
            "question_text": question.get("question", ""),
            "answer": question.get("answer", ""),
            "options": question.get("options"),
            "question_type": question.get("type", "short_answer"),
            "difficulty": question.get("difficulty", "medium"),
            "explanation": question.get("explanation"),
        }

    def submit_quiz(
        self,
        subject_id: int,
        topic_id: Optional[int],
        questions: List[Dict[str, Any]],
        answers: List[str],
        duration_seconds: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Submit a completed quiz and calculate score.

        Args:
            subject_id: Subject ID.
            topic_id: Optional topic ID.
            questions: List of question dicts.
            answers: List of user answers (same order as questions).
            duration_seconds: Time taken.

        Returns:
            Dict with score, correct_count, and results.
        """
        if len(questions) != len(answers):
            raise ValueError("Questions and answers length mismatch")

        correct_count = 0
        results = []

        for idx, (question, user_answer) in enumerate(zip(questions, answers)):
            correct_answer = question.get("answer", "").strip().lower()
            user_answer_clean = user_answer.strip().lower()

            is_correct = correct_answer == user_answer_clean

            if is_correct:
                correct_count += 1

            results.append(
                {
                    "question_index": idx,
                    "question": question.get("question_text", ""),
                    "correct_answer": correct_answer,
                    "user_answer": user_answer,
                    "is_correct": is_correct,
                    "explanation": question.get("explanation"),
                }
            )

        total = len(questions)
        score_percentage = (correct_count / total * 100) if total > 0 else 0

        # Save to database
        quiz_id = save_quiz_result(
            subject_id=subject_id,
            topic_id=topic_id,
            question_count=total,
            correct_count=correct_count,
            score_percentage=score_percentage,
            questions=questions,
            answers=answers,
            duration_seconds=duration_seconds,
        )

        logger.info(
            "Quiz %d submitted: %d/%d correct (%.1f%%)",
            quiz_id,
            correct_count,
            total,
            score_percentage,
        )

        return {
            "quiz_id": quiz_id,
            "score_percentage": round(score_percentage, 1),
            "correct_count": correct_count,
            "total_count": total,
            "results": results,
        }

    def shuffle_questions(self, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Shuffle questions for variety.

        Args:
            questions: List of question dicts.

        Returns:
            Shuffled list.
        """
        shuffled = questions.copy()
        random.shuffle(shuffled)
        return shuffled
