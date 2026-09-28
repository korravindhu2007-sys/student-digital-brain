"""Modern sidebar component for NeuroNote."""

from __future__ import annotations

import streamlit as st

from services.backend import get_app_status

NAV_ITEMS = [
    ("Dashboard", "📊"),
    ("Upload", "📤"),
    ("AI Chat", "🤖"),
    ("Flash Cards", "🃏"),
    ("Study Mode", "📖"),
]


def render_sidebar() -> str:
    """Render the modern sidebar with navigation, status, and info.

    Returns:
        The selected navigation item name.
    """
    status = get_app_status()

    with st.sidebar:
        _render_logo()
        _render_status_badges(status)
        st.divider()
        selected = _render_navigation()
        st.divider()
        _render_system_info(status)
        st.divider()
        _render_storage_info()
        st.divider()
        _render_offline_badge()

    return selected


def _render_logo() -> None:
    """Render the application logo and brand name."""
    cols = st.columns([1, 3])
    with cols[0]:
        st.markdown(
            "<div style='font-size:2rem; text-align:center;'>🧠</div>",
            unsafe_allow_html=True,
        )
    with cols[1]:
        st.markdown(
            "<div style='font-weight:700; font-size:1.3rem; line-height:1.2;'>"
            "NeuroNote</div>"
            "<div style='font-size:0.75rem; color:#6B7280;'>Offline AI Study Companion</div>",
            unsafe_allow_html=True,
        )


def _render_status_badges(status: dict[str, object]) -> None:
    """Render online/offline status badges."""
    cols = st.columns(3)
    with cols[0]:
        db_status = "online" if status.get("database", True) else "offline"
        st.markdown(
            f"<span class='neuro-status'><span class='neuro-status-dot {db_status}'></span>DB</span>",
            unsafe_allow_html=True,
        )
    with cols[1]:
        llm_status = "online" if status.get("ollama", True) else "offline"
        st.markdown(
            f"<span class='neuro-status'><span class='neuro-status-dot {llm_status}'></span>AI</span>",
            unsafe_allow_html=True,
        )
    with cols[2]:
        st.markdown(
            "<span class='neuro-status'><span class='neuro-status-dot online'></span>Offline</span>",
            unsafe_allow_html=True,
        )


def _render_navigation() -> str:
    """Render the navigation menu and return selected item."""
    current = st.session_state.get("page", "Dashboard")

    for icon, label in NAV_ITEMS:
        is_active = current == label
        if st.button(
            f"{icon} {label}",
            key=f"nav_{label}",
            use_container_width=True,
            type="secondary" if not is_active else "primary",
        ):
            st.session_state["page"] = label
            st.rerun()

    return st.session_state.get("page", "Dashboard")


def _render_system_info(status: dict[str, object]) -> None:
    """Render system information in sidebar."""
    st.markdown("**System Info**")
    st.caption(f"Backend: {status.get('backend', 'Ollama + SQLite')}")
    st.caption(f"Mode: {status.get('mode', 'Offline-first')}")
    st.caption(f"Model: {st.session_state.get('ollama_model', 'llama3.2')}")


def _render_storage_info() -> None:
    """Render storage usage information."""
    import os

    db_path = st.session_state.get("database_path", "database/neuronote.db")
    db_size_mb = 0
    try:
        db_size_mb = os.path.getsize(db_path) / (1024 * 1024)
    except (OSError, FileNotFoundError):
        db_size_mb = 0.0

    st.markdown("**Storage**")
    st.caption(f"Database: {db_size_mb:.1f} MB")
    db_status = "Connected" if db_size_mb > 0 else "Empty"
    db_color = "#10B981" if db_size_mb > 0 else "#F59E0B"
    st.markdown(
        f"<span style='color:{db_color}; font-size:0.8rem;'>&#9679; {db_status}</span>",
        unsafe_allow_html=True,
    )


def _render_offline_badge() -> None:
    """Render the offline badge at the bottom."""
    st.markdown(
        "<div style='text-align:center; padding:0.5rem;'><span class='neuro-badge'>🔒 Fully Offline</span></div>",
        unsafe_allow_html=True,
    )
    st.caption("Your PDF data never leaves your device. Powered by local Ollama + SQLite.")
