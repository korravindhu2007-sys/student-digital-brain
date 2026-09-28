"""Revision planning service for NeuroNote."""

from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from src.database.repository import (
    create_revision_session,
    get_revision_plan,
    get_topics_by_subject,
)
from src.llm.engine import LLMEngine
from src.utils.logging import setup_logging

logger = setup_logging(__name__)


class RevisionService:
    """Generate and manage revision plans."""

    def __init__(self) -> None:
        self.llm_engine = LLMEngine()

    def generate_revision_plan(
        self,
        subject_id: int,
        available_days: int,
        hours_per_day: float = 2.0,
    ) -> List[Dict[str, Any]]:
        """Generate a day-by-day revision plan.

        Args:
            subject_id: Subject ID.
            available_days: Number of days available for revision.
            hours_per_day: Study hours per day.

        Returns:
            List of revision session dicts.
        """
        # Get topics for the subject
        topics = get_topics_by_subject(subject_id)

        if not topics:
            logger.warning("No topics found for subject %d", subject_id)
            return []

        # Calculate total available minutes
        total_minutes = int(available_days * hours_per_day * 60)

        # Distribute time across topics based on definition count
        total_definitions = sum(t.get("definition_count", 1) for t in topics)
        if total_definitions == 0:
            total_definitions = len(topics)

        plan: List[Dict[str, Any]] = []
        current_date = date.today()

        for topic in topics:
            # Allocate minutes proportional to definition count
            def_count = topic.get("definition_count", 1)
            allocated_minutes = int((def_count / total_definitions) * total_minutes)
            allocated_minutes = max(allocated_minutes, 30)  # Minimum 30 min

            # Create revision session
            session = {
                "subject_id": subject_id,
                "topic_id": topic["id"],
                "topic_name": topic["name"],
                "planned_date": current_date.isoformat(),
                "duration_minutes": allocated_minutes,
                "definition_count": def_count,
                "completed": False,
            }
            plan.append(session)

            # Save to database
            create_revision_session(
                subject_id=subject_id,
                topic_id=topic["id"],
                planned_date=current_date,
                duration_minutes=allocated_minutes,
            )

            current_date += timedelta(days=1)

        logger.info(
            "Generated revision plan for subject %d: %d sessions over %d days",
            subject_id,
            len(plan),
            available_days,
        )
        return plan

    def get_plan(
        self,
        subject_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """Get revision plan for a date range.

        Args:
            subject_id: Subject ID.
            start_date: Range start (default: today).
            end_date: Range end (default: 30 days from today).

        Returns:
            List of revision session dicts.
        """
        start = start_date or date.today()
        end = end_date or (start + timedelta(days=30))

        return get_revision_plan(subject_id, start, end)

    def mark_completed(self, session_id: int, notes: Optional[str] = None) -> bool:
        """Mark a revision session as completed.

        Args:
            session_id: Revision session ID.
            notes: Optional completion notes.

        Returns:
            True if update succeeded.
        """
        try:
            from src.database.connection import get_db

            with get_db() as conn:
                cursor = conn.execute(
                    """UPDATE revision_history
                       SET completed = 1, notes = ?
                       WHERE id = ?""",
                    (notes, session_id),
                )
                # Check if any row was actually updated
                if cursor.rowcount == 0:
                    logger.warning("Revision session %d not found", session_id)
                    return False
            logger.info("Revision session %d marked completed", session_id)
            return True
        except Exception as e:
            logger.error("Failed to mark session completed: %s", e)
            return False
