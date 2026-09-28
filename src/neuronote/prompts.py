"""Prompt templates for NeuroNote AI Study Companion."""

from typing import Any

SOURCE_BOUNDARY_RULE = """You are ONLY allowed to answer using the provided study material.
If the answer is unavailable,
respond
The uploaded study material does not contain this information.
Never invent facts."""


# ──────────────────────────────────────────────
# Chat Prompts
# ──────────────────────────────────────────────

CHAT_PROMPT = """{source_rule}
Be concise and student-friendly.

Context from PDF:
{context}

Question: {question}

Return JSON:
{{
  "answer": "Your answer based only on the context",
  "confidence": 85,
  "related_topics": ["topic1", "topic2"],
  "suggested_followups": ["Explain more", "Give example", "Compare"]
}}
"""

DOUBT_SOLVER_PROMPT = """{source_rule}
Explain clearly with examples if available.

Context from PDF:
{context}

Doubt/Question: {question}

Return JSON:
{{
  "answer": "Detailed explanation based only on the PDF context",
  "confidence": 80,
  "related_topics": ["related topic 1", "related topic 2"],
  "suggested_followups": ["Explain more", "Give example", "Compare", "Common mistakes"]
}}
"""

EXPLAIN_SIMPLER_PROMPT = """Simplify the following explanation for a 5th-12th grade student.
Use simple language and examples.

Original Answer: {answer}
Context: {context}

Return JSON:
{{
  "simplified_explanation": "Simple explanation here"
}}
"""


# ──────────────────────────────────────────────
# Study Mode Prompt
# ──────────────────────────────────────────────

STUDY_MODE_PROMPT = """{source_rule}
Generate structured study material from the provided PDF content.
Organize into sections. Be concise. Do not add outside knowledge.

PDF Content:
{context}

Return JSON:
{{
  "introduction": "Brief introduction",
  "definitions": ["term: definition"],
  "core_concepts": ["concept explanation"],
  "important_points": ["point 1", "point 2"],
  "examples": ["example 1"],
  "algorithms": ["algorithm if any"],
  "formulae": ["formula if any"],
  "applications": ["application 1"],
  "summary": "Brief summary"
}}
"""


# ──────────────────────────────────────────────
# Flash Cards Prompt
# ──────────────────────────────────────────────

FLASHCARDS_PROMPT = """{source_rule}
Generate 30 flash cards from the provided PDF content.
Each card should have a question (front) and answer (back).
Focus on key concepts, definitions, formulas, and important facts.
Return ONLY valid JSON array.

PDF Content:
{context}

Return JSON array of 30 objects:
[
  {{
    "front": "Question here",
    "back": "Answer here",
    "type": "question|definition|formula",
    "difficulty": "easy|medium|hard"
  }}
]
"""


# ──────────────────────────────────────────────
# Highlights Prompt
# ──────────────────────────────────────────────

HIGHLIGHTS_PROMPT = """{source_rule}
Identify and extract important lines from the provided PDF content.
Focus on: definitions, important sentences, formulae, exam points, algorithms, theorems, key facts.

PDF Content:
{context}

Return JSON:
{{
  "highlights": [
    {{
      "type": "definition|formula|important|algorithm|theorem",
      "text": "The important text",
      "page_number": 1,
      "section_heading": "Section name",
      "context": "Surrounding context"
    }}
  ]
}}
"""


# ──────────────────────────────────────────────
# Formula Sheet Prompt
# ──────────────────────────────────────────────

FORMULA_SHEET_PROMPT = """{source_rule}
Extract all formulae, equations, algorithms, and syntax from the provided PDF content.
For each formula, provide meaning, variable explanations, where it is used, and an example.

PDF Content:
{context}

Return JSON:
{{
  "formulas": [
    {{
      "formula": "Formula text",
      "meaning": "What it means",
      "variables": "Variable explanations",
      "where_used": "Usage context",
      "example": "Example usage",
      "page_number": 1
    }}
  ]
}}
"""


# ──────────────────────────────────────────────
# Semantic Search Prompt
# ──────────────────────────────────────────────

SEMANTIC_SEARCH_PROMPT = """{source_rule}
Search the provided PDF content for information about the query.
Return the most relevant information along with source details.

PDF Content:
{context}

Query: {query}

Return JSON:
{{
  "found": true|false,
  "answer": "Answer based on PDF content",
  "definition": "Definition if applicable",
  "explanation": "Detailed explanation",
  "source_page": 1,
  "source_paragraph": 1,
  "confidence": 85
}}
"""


# ──────────────────────────────────────────────
# Chunking Utilities
# ──────────────────────────────────────────────


def format_prompt(template: str, **kwargs: Any) -> str:
    """Format a prompt template with provided kwargs.

    Args:
        template: Prompt template string with {placeholders}.
        **kwargs: Values to fill placeholders.

    Returns:
        Formatted prompt string.
    """
    try:
        return template.format(source_rule=SOURCE_BOUNDARY_RULE, **kwargs)
    except KeyError as e:
        raise ValueError(f"Missing required prompt parameter: {e}") from e


def get_chat_prompt(question: str, context: str) -> str:
    """Get formatted chat prompt.

    Args:
        question: User question.
        context: Retrieved PDF context.

    Returns:
        Formatted prompt.
    """
    return format_prompt(CHAT_PROMPT, question=question, context=context)


def get_doubt_solver_prompt(question: str, context: str) -> str:
    """Get formatted doubt solver prompt.

    Args:
        question: User question/doubt.
        context: Retrieved PDF context.

    Returns:
        Formatted prompt.
    """
    return format_prompt(DOUBT_SOLVER_PROMPT, question=question, context=context)


def get_study_mode_prompt(context: str) -> str:
    """Get formatted study mode prompt.

    Args:
        context: PDF content.

    Returns:
        Formatted prompt.
    """
    return format_prompt(STUDY_MODE_PROMPT, context=context)


def get_flashcards_prompt(context: str) -> str:
    """Get formatted flashcards prompt.

    Args:
        context: PDF content.

    Returns:
        Formatted prompt.
    """
    return format_prompt(FLASHCARDS_PROMPT, context=context)


def get_highlights_prompt(context: str) -> str:
    """Get formatted highlights prompt.

    Args:
        context: PDF content.

    Returns:
        Formatted prompt.
    """
    return format_prompt(HIGHLIGHTS_PROMPT, context=context)


def get_formula_sheet_prompt(context: str) -> str:
    """Get formatted formula sheet prompt.

    Args:
        context: PDF content.

    Returns:
        Formatted prompt.
    """
    return format_prompt(FORMULA_SHEET_PROMPT, context=context)


def get_semantic_search_prompt(query: str, context: str) -> str:
    """Get formatted semantic search prompt.

    Args:
        query: Search query.
        context: PDF content.

    Returns:
        Formatted prompt.
    """
    return format_prompt(SEMANTIC_SEARCH_PROMPT, query=query, context=context)


def structured_extraction_prompt(text: str, metadata: dict[str, object] | None = None) -> str:
    metadata = metadata or {}
    return format_prompt(
        """{source_rule}
Extract a compact JSON study index from the provided study material.

Subject: {subject}
Topic: {topic}

Study material:
{context}

Return JSON with keys: subject, topic, summary, topics, concepts.
Each concept must include concept, definition, importance, and related_concepts.""",
        subject=str(metadata.get("subject", "General")),
        topic=str(metadata.get("topic", "General")),
        context=text[:12000],
    )


def revision_prompt(text: str, subject: str = "General", topic: str = "General") -> str:
    return format_prompt(
        """{source_rule}
Create a revision outline only from the provided study material.

Subject: {subject}
Topic: {topic}

Study material:
{context}

Return JSON with keys: mind_map, important_topics, definitions, study_notes, question_bank.""",
        subject=subject,
        topic=topic,
        context=text[:12000],
    )
