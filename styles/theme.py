"""Theme configuration for NeuroNote UI."""

from __future__ import annotations

import streamlit as st

DARK_THEME = {
    "primaryColor": "#7C3AED",
    "backgroundColor": "#0F0F13",
    "secondaryBackgroundColor": "#1A1A23",
    "textColor": "#E8E8ED",
    "font": "Inter, system-ui, -apple-system, sans-serif",
    "borderRadius": "12px",
}

LIGHT_THEME = {
    "primaryColor": "#7C3AED",
    "backgroundColor": "#F8F9FA",
    "secondaryBackgroundColor": "#FFFFFF",
    "textColor": "#1A1A2E",
    "font": "Inter, system-ui, -apple-system, sans-serif",
    "borderRadius": "12px",
}


def get_theme(is_dark: bool | None = None) -> dict[str, str]:
    """Get theme configuration.

    Args:
        is_dark: Whether dark mode is active. If None, check session state.

    Returns:
        Theme dict.
    """
    if is_dark is None:
        is_dark = st.session_state.get("theme", "dark") == "dark"
    return DARK_THEME if is_dark else LIGHT_THEME


def get_bg_color(is_dark: bool | None = None) -> str:
    """Get background color based on theme."""
    return get_theme(is_dark)["backgroundColor"]


def get_secondary_bg(is_dark: bool | None = None) -> str:
    """Get secondary background color."""
    return get_theme(is_dark)["secondaryBackgroundColor"]


def get_text_color(is_dark: bool | None = None) -> str:
    """Get text color."""
    return get_theme(is_dark)["textColor"]


def is_dark_mode() -> bool:
    """Check if dark mode is active."""
    return st.session_state.get("theme", "dark") == "dark"
