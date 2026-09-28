"""Empty state component for NeuroNote."""

from __future__ import annotations

import streamlit as st


def render_empty_state(
    title: str,
    description: str,
    icon: str = "📂",
    action_label: str | None = None,
    action_key: str | None = None,
) -> bool:
    """Render an empty state with optional action button.

    Args:
        title: The title text.
        description: The description text.
        icon: Emoji icon.
        action_label: Optional button text.
        action_key: Optional button key.

    Returns:
        True if the action button was clicked, False otherwise.
    """
    muted = "#6B7280"

    st.markdown(
        f"""
        <div class="neuro-empty">
            <div class="neuro-empty-icon">{icon}</div>
            <div class="neuro-empty-title">{title}</div>
            <p style="color:{muted}; margin-bottom:1.5rem;">{description}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    clicked = False
    if action_label and action_key:
        if st.button(action_label, key=action_key, type="primary", use_container_width=True):
            clicked = True

    return clicked


def render_welcome_state() -> None:
    """Render the welcome state for new users with no documents."""
    st.markdown(
        """
    <div class="neuro-empty">
        <div class="neuro-empty-icon">🧠</div>
        <div class="neuro-empty-title">Welcome to NeuroNote</div>
        <p style="color:#6B7280; margin-bottom:2rem;">
            Your offline AI study companion. Upload a PDF to get started.
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    cols = st.columns(3)
    with cols[0]:
        st.markdown(
            "<div class='neuro-card-dashboard'>"
            "<div style='font-size:1.5rem; margin-bottom:0.5rem;'>📤</div>"
            "<div style='font-weight:500;'>Upload PDF</div>"
            "<div style='font-size:0.8rem; color:#6B7280;'>Drag & drop or browse</div>"
            "</div>",
            unsafe_allow_html=True,
        )
    with cols[1]:
        st.markdown(
            "<div class='neuro-card-dashboard'>"
            "<div style='font-size:1.5rem; margin-bottom:0.5rem;'>🤖</div>"
            "<div style='font-weight:500;'>Ask Questions</div>"
            "<div style='font-size:0.8rem; color:#6B7280;'>AI chat over your PDFs</div>"
            "</div>",
            unsafe_allow_html=True,
        )
    with cols[2]:
        st.markdown(
            "<div class='neuro-card-dashboard'>"
            "<div style='font-size:1.5rem; margin-bottom:0.5rem;'>📖</div>"
            "<div style='font-weight:500;'>Study Mode</div>"
            "<div style='font-size:0.8rem; color:#6B7280;'>Flash cards & formulas</div>"
            "</div>",
            unsafe_allow_html=True,
        )
