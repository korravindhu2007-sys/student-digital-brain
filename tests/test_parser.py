"""Tests for parser module."""


from src.parser.json_parser import JSONParser
from src.parser.text_processor import TextProcessor


class TestTextProcessor:
    """Test text cleaning and chunking."""

    def setup_method(self):
        """Set up test fixtures."""
        self.processor = TextProcessor()

    def test_clean_text_removes_page_numbers(self):
        """Test that page numbers are removed."""
        text = "Some content\n\n42\n\nMore content"
        cleaned = self.processor.clean_text(text)
        assert "42" not in cleaned or cleaned.count("42") == 0

    def test_clean_text_normalizes_whitespace(self):
        """Test whitespace normalization."""
        text = "Hello   world\n\n\n\n\nHow are you?"
        cleaned = self.processor.clean_text(text)
        assert "   " not in cleaned  # No triple spaces
        assert "\n\n\n" not in cleaned  # No triple newlines

    def test_clean_text_removes_control_chars(self):
        """Test removal of control characters."""
        text = "Hello\x00world\x01test"
        cleaned = self.processor.clean_text(text)
        assert "\x00" not in cleaned
        assert "\x01" not in cleaned

    def test_chunk_text_splits_correctly(self):
        """Test text chunking."""
        text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        chunks = self.processor.chunk_text(text)
        assert len(chunks) >= 1
        assert all(isinstance(c, str) for c in chunks)

    def test_chunk_text_empty_input(self):
        """Test chunking empty text."""
        chunks = self.processor.chunk_text("")
        assert chunks == []

    def test_estimate_chunks(self):
        """Test chunk estimation."""
        text = "A" * 10000  # ~2500 tokens
        estimate = self.processor.estimate_chunks(text)
        assert estimate >= 1


class TestJSONParser:
    """Test JSON parsing and validation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = JSONParser()

    def test_parse_raw_json_valid(self):
        """Test parsing valid JSON."""
        json_str = '{"concepts": [{"term": "Test", "definition": "A test", "importance": "high"}]}'
        result = self.parser.parse_raw_json(json_str)
        assert result is not None
        assert "concepts" in result

    def test_parse_raw_json_with_markdown(self):
        """Test parsing JSON wrapped in markdown code block."""
        json_str = '```json\n{"term": "Test"}\n```'
        result = self.parser.parse_raw_json(json_str)
        assert result is not None
        assert result.get("term") == "Test"

    def test_parse_raw_json_invalid(self):
        """Test parsing invalid JSON."""
        result = self.parser.parse_raw_json("not json at all")
        assert result is None

    def test_validate_concept_valid(self):
        """Test validating a valid concept."""
        concept = {
            "term": "Mitosis",
            "definition": "Cell division process",
            "importance": "high",
        }
        is_valid, errors = self.parser.validate_concept(concept)
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_concept_missing_term(self):
        """Test validating concept with missing term."""
        concept = {"definition": "Cell division", "importance": "high"}
        is_valid, errors = self.parser.validate_concept(concept)
        assert is_valid is False
        assert any("term" in e for e in errors)

    def test_validate_concept_invalid_importance(self):
        """Test validating concept with invalid importance."""
        concept = {
            "term": "Test",
            "definition": "A test concept",
            "importance": "invalid",
        }
        is_valid, errors = self.parser.validate_concept(concept)
        assert is_valid is False

    def test_validate_question_valid_mcq(self):
        """Test validating a valid MCQ."""
        question = {
            "question": "What is 2+2?",
            "answer": "4",
            "type": "multiple_choice",
            "options": ["3", "4", "5", "6"],
        }
        is_valid, errors = self.parser.validate_question(question)
        assert is_valid is True

    def test_validate_question_missing_options(self):
        """Test validating MCQ without options."""
        question = {
            "question": "What is 2+2?",
            "answer": "4",
            "type": "multiple_choice",
        }
        is_valid, errors = self.parser.validate_question(question)
        assert is_valid is False

    def test_normalize_concept(self):
        """Test concept normalization."""
        concept = {
            "term": "  Mitosis  ",
            "definition": "Cell division process",
            "importance": "HIGH",
            "related_concepts": ["Meiosis"],
        }
        normalized = self.parser.normalize_concept(concept)
        assert normalized["term"] == "Mitosis"
        assert normalized["importance"] == "high"  # Normalized from HIGH

    def test_parse_extraction_output_list(self):
        """Test parsing list format output."""
        raw = '[{"term": "A", "definition": "Definition A is here", "importance": "high"}]'
        result = self.parser.parse_extraction_output(raw)
        assert len(result["concepts"]) == 1

    def test_parse_extraction_output_dict(self):
        """Test parsing dict format output."""
        raw = '{"concepts": [{"term": "A", "definition": "Definition A is here", "importance": "high"}], "questions": []}'
        result = self.parser.parse_extraction_output(raw)
        assert len(result["concepts"]) == 1
        assert len(result["questions"]) == 0
