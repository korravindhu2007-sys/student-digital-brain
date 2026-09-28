"""Intent-specific prompt templates for NeuroNote AI Engine.

Every prompt enforces strict source-only answering.
Ollama must NEVER use its own knowledge.
"""

from __future__ import annotations

from typing import Any

SYSTEM_PROMPT = """You are an offline study assistant.
Answer ONLY using the supplied study material.
Never use external knowledge.
Never invent facts.
If the answer is unavailable, respond:
"The uploaded document does not contain enough information to answer this question."
Always include source page references."""


def _build_prompt(template: str, **kwargs: Any) -> str:
    """Build a prompt with the system prefix and context.

    Args:
        template: The intent-specific template.
        **kwargs: Template variables.

    Returns:
        Complete prompt string.
    """
    context = kwargs.pop("context", "")
    question = kwargs.pop("question", "")
    extras = "".join(f"\n{k}: {v}" for k, v in kwargs.items() if v)

    return f"""{SYSTEM_PROMPT}

Context from study material:
{context}

Question: {question}{extras}

Provide your response in the following JSON format:
{{"answer": "Your answer here", "confidence": 85, "related_topics": ["topic1", "topic2"], "suggested_followups": ["followup1", "followup2"], "source_document": "document name", "source_page": 1, "source_paragraph": 1}}"""


class PromptTemplates:
    """Reusable intent-specific prompt templates."""

    @staticmethod
    def definition(context: str, question: str) -> str:
        """Prompt for definition-type questions."""
        return _build_prompt(
            """Provide a clear definition based ONLY on the context.
Include:
- Definition
- Key characteristics
- Source page reference""",
            context=context,
            question=question,
            intent="definition",
        )

    @staticmethod
    def explanation(context: str, question: str) -> str:
        """Prompt for explanation-type questions."""
        return _build_prompt(
            """Explain the concept based ONLY on the context.
Include:
- Clear explanation
- How it works
- Why it matters
- Source page reference""",
            context=context,
            question=question,
            intent="explanation",
        )

    @staticmethod
    def comparison(context: str, question: str) -> str:
        """Prompt for comparison-type questions."""
        return _build_prompt(
            """Compare and contrast based ONLY on the context.
Include:
- Key similarities
- Key differences
- When to use each
- Source page reference""",
            context=context,
            question=question,
            intent="comparison",
        )

    @staticmethod
    def example(context: str, question: str) -> str:
        """Prompt for example-type questions."""
        return _build_prompt(
            """Provide examples based ONLY on the context.
Include:
- Concrete examples from the material
- Step-by-step walkthrough if applicable
- Source page reference""",
            context=context,
            question=question,
            intent="example",
        )

    @staticmethod
    def formula(context: str, question: str) -> str:
        """Prompt for formula-type questions."""
        return _build_prompt(
            """Extract and explain the formula based ONLY on the context.
Include:
- The formula/equation
- What each variable means
- How it is used
- Source page reference""",
            context=context,
            question=question,
            intent="formula",
        )

    @staticmethod
    def algorithm(context: str, question: str) -> str:
        """Prompt for algorithm-type questions."""
        return _build_prompt(
            """Describe the algorithm based ONLY on the context.
Include:
- Algorithm name
- Steps/procedure
- Time/space complexity if mentioned
- Source page reference""",
            context=context,
            question=question,
            intent="algorithm",
        )

    @staticmethod
    def advantage_disadvantage(context: str, question: str) -> str:
        """Prompt for advantages/disadvantages questions."""
        return _build_prompt(
            """List advantages and disadvantages based ONLY on the context.
Include:
- Advantages with explanation
- Disadvantages with explanation
- Source page reference""",
            context=context,
            question=question,
            intent="advantages_disadvantages",
        )

    @staticmethod
    def application(context: str, question: str) -> str:
        """Prompt for application-type questions."""
        return _build_prompt(
            """Describe applications and use cases based ONLY on the context.
Include:
- Real-world applications
- Where it is used
- Source page reference""",
            context=context,
            question=question,
            intent="application",
        )

    @staticmethod
    def general_chat(context: str, question: str) -> str:
        """Default chat prompt for general questions."""
        return _build_prompt(
            """Answer the question using ONLY the context provided.
Be concise and student-friendly.
Include source page references.""",
            context=context,
            question=question,
            intent="general",
        )

    @staticmethod
    def doubt_solver(context: str, question: str) -> str:
        """Prompt for the doubt solver mode."""
        return _build_prompt(
            """You are a helpful tutor. Explain this concept clearly based ONLY on the context.
Include:
- Simple definition
- Explanation in easy language
- Example from the material if available
- Source page reference
If the material does not cover this, say so.""",
            context=context,
            question=question,
            intent="doubt_solver",
        )

    @staticmethod
    def study_notes(context: str) -> str:
        """Prompt for generating structured study notes."""
        return f"""{SYSTEM_PROMPT}

Generate structured study material from the provided PDF content.
Organize into sections. Be concise. Maximum 150 words per topic.

PDF Content:
{context}

Return JSON with these sections:
{{
  "introduction": "Brief introduction",
  "definitions": [{{"term": "term", "definition": "definition", "page": 1}}],
  "core_concepts": [{{"concept": "concept", "explanation": "explanation", "page": 1}}],
  "important_points": ["point 1", "point 2"],
  "examples": [{{"example": "example", "page": 1}}],
  "applications": ["application 1"],
  "algorithms": [{{"name": "algorithm", "steps": ["step1"], "complexity": "O(n)"}}],
  "formulae": [{{"formula": "formula", "meaning": "meaning", "page": 1}}],
  "hardware_software": [],
  "summary": "Brief summary"
}}"""

    @staticmethod
    def flash_cards(context: str) -> str:
        """Prompt for generating flash cards."""
        return f"""{SYSTEM_PROMPT}

Generate 30 flash cards from the provided PDF content.
Each card: question (front) and answer (back).
Focus on key concepts, definitions, formulas, important facts.
Include difficulty level (easy/medium/hard).

PDF Content:
{context}

Return JSON array of exactly 30 objects:
[
  {{
    "front": "Question here",
    "back": "Answer here",
    "type": "definition|concept|formula|example",
    "difficulty": "easy|medium|hard",
    "page_number": 1
  }}
]"""

    @staticmethod
    def highlights(context: str) -> str:
        """Prompt for extracting highlights."""
        return f"""{SYSTEM_PROMPT}

Identify important lines from the provided PDF content.
Focus on: definitions, important sentences, formulae, exam points, algorithms, theorems, key facts.

PDF Content:
{context}

Return JSON:
{{
  "highlights": [
    {{
      "type": "definition|formula|important|algorithm|theorem|exam_tip|warning",
      "text": "The important text",
      "page_number": 1,
      "reason": "Why this is important"
    }}
  ]
}}"""

    @staticmethod
    def formula_sheet(context: str) -> str:
        """Prompt for extracting formulas."""
        return f"""{SYSTEM_PROMPT}

Extract all formulae, equations, algorithms, and syntax from the provided PDF content.
For each: meaning, variables, where used, example.

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
}}"""

    @staticmethod
    def detect_intent(question: str) -> str:
        """Detect the intent of a user question.

        Args:
            question: User's question text.

        Returns:
            Intent type string.
        """
        q = question.lower().strip()

        # Definition patterns
        if q.startswith(("what is", "what are", "define", "definition of", "meaning of", "what does")):
            return "definition"

        # Comparison patterns
        if q.startswith(("difference", "compare", "differentiate", "vs", "versus", "distinguish")):
            return "comparison"

        # Explanation patterns
        if q.startswith(("explain", "how does", "how do", "why is", "why does", "describe", "tell me about")):
            return "explanation"

        # Example patterns
        if q.startswith(("example", "give example", "show example", "instance")):
            return "example"

        # Formula patterns
        if q.startswith(("formula", "equation", "calculate", "what is the formula")):
            return "formula"

        # Algorithm patterns
        if q.startswith(("algorithm", "steps", "procedure", "how to", "process")):
            return "algorithm"

        # Advantage/Disadvantage patterns
        if any(word in q for word in ["advantage", "disadvantage", "pros", "cons", "benefit", "drawback"]):
            return "advantage_disadvantage"

        # Application patterns
        if q.startswith(("application", "where is", "use of", "usage")):
            return "application"

        return "general_chat"


# Convenience functions
def get_chat_prompt(context: str, question: str) -> str:
    """Get the appropriate chat prompt based on question intent."""
    intent = PromptTemplates.detect_intent(question)
    template_map = {
        "definition": PromptTemplates.definition,
        "comparison": PromptTemplates.comparison,
        "explanation": PromptTemplates.explanation,
        "example": PromptTemplates.example,
        "formula": PromptTemplates.formula,
        "algorithm": PromptTemplates.algorithm,
        "advantage_disadvantage": PromptTemplates.advantage_disadvantage,
        "application": PromptTemplates.application,
        "general_chat": PromptTemplates.general_chat,
    }
    formatter = template_map.get(intent, PromptTemplates.general_chat)
    return formatter(context, question)


def get_doubt_solver_prompt(context: str, question: str) -> str:
    """Get the doubt solver prompt."""
    return PromptTemplates.doubt_solver(context, question)


def get_study_notes_prompt(context: str) -> str:
    """Get the study notes generation prompt."""
    return PromptTemplates.study_notes(context)


def get_flash_cards_prompt(context: str) -> str:
    """Get the flash cards generation prompt."""
    return PromptTemplates.flash_cards(context)


def get_highlights_prompt(context: str) -> str:
    """Get the highlights extraction prompt."""
    return PromptTemplates.highlights(context)


def get_formula_sheet_prompt(context: str) -> str:
    """Get the formula sheet generation prompt."""
    return PromptTemplates.formula_sheet(context)
