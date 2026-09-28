"""Top bar component for NeuroNote."""

from __future__ import annotations

import streamlit as st

from styles.theme import is_dark_mode


def render_topbar(
    title: str | None = None,
    doc_name: str | None = None,
    total_pages: int | None = None,
    model: str | None = None,
) -> None:
    """Render the top bar with document info and controls.

    Args:
        title: Page title override.
        doc_name: Current document name.
        total_pages: Total pages in document.
        model: Current AI model name.
    """
    if model is None:
        model = st.session_state.get("ollama_model", "llama3.2")

    cols = st.columns([3, 1, 1, 1, 1])

    with cols[0]:
        if title:
            st.markdown(f"**{title}**")
        elif doc_name:
            st.markdown(f"**📄 {doc_name}**")
            if total_pages:
                st.caption(f"{total_pages} pages")

    with cols[1]:
        if model:
            st.markdown(
                f"<span class='neuro-badge'>🤖 {model}</span>",
                unsafe_allow_html=True,
            )

    with cols[2]:
        st.markdown(
            "<span class='neuro-badge'>🔒 Offline</span>",
            unsafe_allow_html=True,
        )

    with cols[3]:
        _render_theme_toggle()

    with cols[4]:
        if st.button("🔄", help="Refresh", key="topbar_refresh"):
            st.rerun()


def _render_theme_toggle() -> None:
    """Render the theme toggle button."""
    dark = is_dark_mode()
    icon = "🌙" if dark else "☀️"
    if st.button(f"{icon}", help=f"Switch to {'Light' if dark else 'Dark'} mode", key="theme_toggle"):
        st.session_state["theme"] = "light" if dark else "dark"
        st.rerun()
