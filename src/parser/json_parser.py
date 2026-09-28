"""JSON schema parser and validator for LLM output."""

import json
from typing import Any, Dict, List, Optional, Tuple

from src.utils.logging import setup_logging

logger = setup_logging(__name__)


class JSONParser:
    """Parse and validate JSON output from the LLM.

    Validates extracted concepts, definitions, topics, and questions
    against the expected schema.
    """

    REQUIRED_CONCEPT_FIELDS = ["term", "definition", "importance"]
    REQUIRED_QUESTION_FIELDS = ["question", "answer", "type"]
    VALID_IMPORTANCE = ["high", "medium", "low"]
    VALID_QUESTION_TYPES = ["multiple_choice", "true_false", "short_answer"]
    VALID_DIFFICULTY = ["easy", "medium", "hard"]

    def parse_raw_json(self, json_string: str) -> Optional[Dict[str, Any]]:
        """Parse a raw JSON string from the LLM.

        Args:
            json_string: Raw JSON string, possibly with markdown fences.

        Returns:
            Parsed dict or None if parsing fails.
        """
        # Clean markdown code blocks
        text = json_string.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]

        try:
            parsed = json.loads(text.strip())
            return parsed
        except json.JSONDecodeError as e:
            logger.warning("JSON parse error: %s", e)
            return None

    def validate_concept(self, concept: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate a single concept object.

        Args:
            concept: Concept dict from LLM.

        Returns:
            Tuple of (is_valid: bool, errors: List[str]).
        """
        errors: List[str] = []

        for field in self.REQUIRED_CONCEPT_FIELDS:
            if field not in concept:
                errors.append(f"Missing required field: '{field}'")

        if "term" in concept:
            if not isinstance(concept["term"], str) or len(concept["term"]) < 1:
                errors.append("'term' must be a non-empty string")

        if "definition" in concept:
            if not isinstance(concept["definition"], str) or len(concept["definition"]) < 10:
                errors.append("'definition' must be a string with at least 10 characters")

        if "importance" in concept:
            if concept["importance"] not in self.VALID_IMPORTANCE:
                errors.append(
                    f"'importance' must be one of {self.VALID_IMPORTANCE}, "
                    f"got '{concept.get('importance')}'"
                )

        if "related_concepts" in concept:
            if not isinstance(concept["related_concepts"], list):
                errors.append("'related_concepts' must be a list")

        return len(errors) == 0, errors

    def validate_question(self, question: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate a single question object.

        Args:
            question: Question dict from LLM.

        Returns:
            Tuple of (is_valid: bool, errors: List[str]).
        """
        errors: List[str] = []

        for field in self.REQUIRED_QUESTION_FIELDS:
            if field not in question:
                errors.append(f"Missing required field: '{field}'")

        if "type" in question:
            if question["type"] not in self.VALID_QUESTION_TYPES:
                errors.append(
                    f"'type' must be one of {self.VALID_QUESTION_TYPES}, "
                    f"got '{question.get('type')}'"
                )

        if "difficulty" in question:
            if question["difficulty"] not in self.VALID_DIFFICULTY:
                errors.append(f"'difficulty' must be one of {self.VALID_DIFFICULTY}")

        # For multiple choice, options are required
        if question.get("type") == "multiple_choice":
            if "options" not in question:
                errors.append("'options' is required for multiple_choice questions")
            elif not isinstance(question["options"], list) or len(question["options"]) < 2:
                errors.append("'options' must be a list with at least 2 items for MCQs")

        return len(errors) == 0, errors

    def validate_concept_list(self, data: Any) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Validate a list of concepts from LLM output.

        Args:
            data: Parsed JSON data (should be list of concepts).

        Returns:
            Tuple of (valid_concepts: List, invalid_concepts: List).
        """
        valid: List[Dict[str, Any]] = []
        invalid: List[Dict[str, Any]] = []

        if not isinstance(data, list):
            logger.warning("Expected list of concepts, got %s", type(data))
            return valid, invalid

        for idx, concept in enumerate(data):
            if not isinstance(concept, dict):
                invalid.append({"index": idx, "error": "Not a dict", "data": concept})
                continue

            is_valid, errors = self.validate_concept(concept)
            if is_valid:
                valid.append(concept)
            else:
                invalid.append({"index": idx, "errors": errors, "data": concept})

        logger.info(
            "Validated %d/%d concepts (valid=%d, invalid=%d)",
            len(data),
            len(data),
            len(valid),
            len(invalid),
        )
        return valid, invalid

    def normalize_concept(self, concept: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize a concept to standard format.

        Args:
            concept: Raw concept dict.

        Returns:
            Normalized concept dict.
        """
        importance = concept.get("importance", "medium")
        # Normalize importance to lowercase
        if isinstance(importance, str):
            importance = importance.lower()
            if importance not in self.VALID_IMPORTANCE:
                importance = "medium"

        return {
            "term": concept.get("term", "").strip(),
            "definition": concept.get("definition", "").strip(),
            "subject": concept.get("subject", ""),
            "importance": importance,
            "related_concepts": concept.get("related_concepts", []),
            "context": concept.get("context"),
            "source_page": concept.get("source_page"),
        }

    def parse_extraction_output(self, raw_json: str) -> Dict[str, Any]:
        """Parse full LLM extraction output.

        Handles both single document and batch formats.

        Args:
            raw_json: Raw JSON string from LLM.

        Returns:
            Dict with 'concepts', 'topics', 'questions' lists.
        """
        parsed = self.parse_raw_json(raw_json)
        if parsed is None:
            return {"concepts": [], "topics": [], "questions": []}

        result: Dict[str, Any] = {"concepts": [], "topics": [], "questions": []}

        # Handle array format
        if isinstance(parsed, list):
            valid_concepts, _ = self.validate_concept_list(parsed)
            result["concepts"] = [self.normalize_concept(c) for c in valid_concepts]
            return result

        # Handle dict format with named sections
        if isinstance(parsed, dict):
            # Concepts
            concepts = parsed.get("concepts", parsed.get("extracted_concepts", []))
            if isinstance(concepts, list):
                valid_c, _ = self.validate_concept_list(concepts)
                result["concepts"] = [self.normalize_concept(c) for c in valid_c]

            # Topics
            topics = parsed.get("topics", parsed.get("identified_topics", []))
            if isinstance(topics, list):
                result["topics"] = topics

            # Questions
            questions = parsed.get("questions", parsed.get("generated_questions", []))
            if isinstance(questions, list):
                valid_q: List[Dict[str, Any]] = []
                for q in questions:
                    is_valid, _ = self.validate_question(q)
                    if is_valid:
                        valid_q.append(q)
                result["questions"] = valid_q

        return result
