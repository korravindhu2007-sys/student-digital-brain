"""Chat box component for NeuroNote."""

from __future__ import annotations

from typing import Any

import streamlit as st


def render_chat_message(
    role: str,
    content: str,
    sources: list[dict[str, Any]] | None = None,
    confidence: int = 0,
    followups: list[str] | None = None,
    related_topics: list[str] | None = None,
    message_id: str = "",
) -> None:
    """Render a chat message with optional sources and followups.

    Args:
        role: 'user' or 'assistant'.
        content: Message text content.
        sources: List of source citations.
        confidence: Confidence score (0-100).
        followups: Suggested follow-up questions.
        related_topics: Related topic suggestions.
        message_id: Unique message identifier.
    """
    is_user = role == "user"
    msg_class = "neuro-user-msg" if is_user else "neuro-assistant-msg"
    avatar = "🧑" if is_user else "🤖"
    name = "You" if is_user else "NeuroNote"

    st.markdown(
        f"""
        <div class="{msg_class} neuro-fade-in">
            <div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:0.5rem;">
                <span style="font-size:1.2rem;">{avatar}</span>
                <span style="font-weight:600;">{name}</span>
                {f'<span class="neuro-badge">Confidence: {confidence}%</span>' if not is_user and confidence > 0 else ""}
            </div>
            <div style="line-height:1.6;">{content}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if sources and not is_user:
        st.markdown("##### 📚 Sources")
        for source in sources:
            _render_source(source)

    if followups and not is_user:
        st.markdown("##### 💡 Follow-up Questions")
        cols = st.columns(3)
        for i, followup in enumerate(followups):
            with cols[i % 3]:
                if st.button(
                    followup[:40] + "..." if len(followup) > 40 else followup,
                    key=f"followup_{message_id}_{i}",
                    use_container_width=True,
                ):
                    st.session_state["pending_question"] = followup
                    st.rerun()

    if related_topics and not is_user:
        st.markdown("##### 🔗 Related Topics")
        cols = st.columns(len(related_topics))
        for i, topic in enumerate(related_topics):
            with cols[i]:
                if st.button(
                    topic,
                    key=f"topic_{message_id}_{i}",
                    use_container_width=True,
                ):
                    st.session_state["pending_question"] = f"Tell me more about {topic}"
                    st.rerun()


def _render_source(source: dict[str, Any]) -> None:
    """Render a single source citation."""
    from components.pdf_viewer import render_source_citation

    render_source_citation(source)


def render_chat_input() -> str | None:
    """Render the chat input area.

    Returns:
        The submitted question text, or None.
    """
    question = st.chat_input(
        "Ask anything about your uploaded PDF...",
        key="chat_input_main",
    )
    return question


def render_conversation_item(
    session_id: str,
    title: str,
    date: str,
    is_active: bool,
    message_count: int,
) -> None:
    """Render a conversation history item.

    Args:
        session_id: Session identifier.
        title: Conversation title.
        date: Date string.
        is_active: Whether this is the active conversation.
        message_count: Number of messages.
    """

    cols = st.columns([3, 1])
    with cols[0]:
        if st.button(
            f"{'💬' if not is_active else '🗨️'} {title}",
            key=f"conv_{session_id}",
            use_container_width=True,
        ):
            st.session_state["chat_session"] = session_id
            st.rerun()
    with cols[1]:
        st.caption(f"{message_count} msgs")
