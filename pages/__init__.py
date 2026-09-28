"""NeuroNote pages package - active pages."""

from pages.dashboard import render_dashboard
from pages.AI_Chat import render_ai_chat
from pages.Flash_Cards import render_flash_cards
from pages.study_mode import render_study_mode
from pages.upload import render_upload

__all__ = [
    "render_dashboard",
    "render_ai_chat",
    "render_flash_cards",
    "render_study_mode",
    "render_upload",
]
