"""Modern card components for NeuroNote."""

from __future__ import annotations

from typing import Any

import streamlit as st


def stat_card(label: str, value: str | int, icon: str = "", delta: str | None = None) -> None:
    """Render a statistics card.

    Args:
        label: Metric label.
        value: Metric value.
        icon: Optional emoji icon.
        delta: Optional delta string.
    """
    st.markdown(
        f"""
        <div class='neuro-card-dashboard'>
            <div style='font-size:1.5rem; margin-bottom:0.5rem;'>{icon}</div>
            <div class='neuro-stat-value'>{value}</div>
            <div class='neuro-stat-label'>{label}</div>
            {f'<div style="color:#10B981; font-size:0.8rem; margin-top:0.25rem;">{delta}</div>' if delta else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )


def action_card(title: str, description: str, icon: str, key: str) -> bool:
    """Render a quick action card button.

    Args:
        title: Action title.
        description: Action description.
        icon: Emoji icon.
        key: Button key.

    Returns:
        True if clicked.
    """
    clicked = st.button(
        f"{icon} **{title}**\n\n{description}",
        key=key,
        use_container_width=True,
    )
    return clicked


def document_card(
    doc: dict[str, Any],
    show_actions: bool = True,
) -> None:
    """Render a document info card with actions.

    Args:
        doc: Document dict.
        show_actions: Whether to show action buttons.
    """
    name = doc.get("source_name") or doc.get("filename", "Unknown")
    pages = doc.get("page_count") or doc.get("pages", 0)
    subject = doc.get("subject", "General")
    topic = doc.get("topic", "General")
    doc_id = doc.get("id") or doc.get("document_id", 0)
    status = doc.get("status", "processed")

    st.markdown(
        f"""
        <div class='neuro-card'>
            <div style="display:flex; justify-content:space-between; align-items:start;">
                <div>
                    <div style="font-weight:600; margin-bottom:0.25rem;">📄 {name}</div>
                    <div style="font-size:0.85rem; color:#6B7280;">
                        {subject} / {topic}
                    </div>
                    <div style="font-size:0.8rem; color:#6B7280; margin-top:0.25rem;">
                        Pages: {pages}
                    </div>
                </div>
                <span class="neuro-badge">{status.title()}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if show_actions and doc_id:
        cols = st.columns(4)
        with cols[0]:
            if st.button("🤖 Chat", key=f"chat_{doc_id}", use_container_width=True):
                st.session_state["page"] = "AI Chat"
                st.session_state["chat_document_id"] = doc_id
                st.rerun()
        with cols[1]:
            if st.button("📖 Study", key=f"study_{doc_id}", use_container_width=True):
                st.session_state["page"] = "Study Mode"
                st.session_state["study_document_id"] = doc_id
                st.rerun()
        with cols[2]:
            if st.button("🃏 Cards", key=f"cards_{doc_id}", use_container_width=True):
                st.session_state["page"] = "Flash Cards"
                st.session_state["flashcard_document_id"] = doc_id
                st.rerun()
        with cols[3]:
            if st.button("🗑️", key=f"delete_{doc_id}", use_container_width=True):
                st.session_state[f"delete_{doc_id}"] = True
                st.rerun()


def topic_card(title: str, content: str, icon: str = "📌") -> None:
    """Render a topic/study note card.

    Args:
        title: Topic title.
        content: Topic content.
        icon: Emoji icon.
    """
    with st.expander(f"{icon} {title}", expanded=False):
        st.markdown(content)
