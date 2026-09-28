"""AI Chat page for NeuroNote - ChatGPT-like experience."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

import streamlit as st

from components.chat_box import render_chat_input, render_chat_message, render_conversation_item
from components.empty_state import render_empty_state
from components.notifications import notify_error, notify_info
from components.topbar import render_topbar
from services.backend import answer_question, get_pdf_options
from styles.custom_css import inject_custom_css


def _init_session_state() -> None:
    """Initialize chat session state."""
    if "chat_sessions" not in st.session_state:
        st.session_state["chat_sessions"] = {}
    if "chat_session" not in st.session_state:
        st.session_state["chat_session"] = "default"
    if "chat_messages" not in st.session_state:
        st.session_state["chat_messages"] = []
    if "chat_document_id" not in st.session_state:
        st.session_state["chat_document_id"] = None
    if "pending_question" not in st.session_state:
        st.session_state["pending_question"] = None


def _get_active_session_id() -> str:
    """Get the active session ID."""
    return st.session_state.get("chat_session", "default")


def _get_document_options() -> tuple[dict[int, str], list[dict[str, Any]]]:
    """Get document options for the chat.

    Returns:
        Tuple of (id_to_name_map, documents_list).
    """
    try:
        options = get_pdf_options()
        documents = options.get("documents", [])
        id_to_name: dict[int, str] = {}
        for doc in documents:
            doc_id = int(doc.get("id") or doc.get("document_id", 0))
            name = doc.get("source_name") or doc.get("filename", "Unknown")
            id_to_name[doc_id] = name
        return id_to_name, documents
    except Exception:
        return {}, []


def render_ai_chat() -> None:
    """Render the AI Chat page with three-panel layout."""
    inject_custom_css()
    _init_session_state()

    id_to_name, documents = _get_document_options()

    render_topbar(title="🤖 AI Chat")

    if not documents:
        if render_empty_state(
            "No Documents Found",
            "Upload a PDF to begin chatting with AI.",
            icon="📄",
            action_label="📤 Upload PDF",
            action_key="go_upload_empty",
        ):
            st.session_state["page"] = "Upload"
            st.rerun()
        return

    # Three-panel layout
    left_col, center_col, right_col = st.columns([1.2, 2.5, 1.3])

    with left_col:
        _render_conversation_panel(id_to_name)
    with center_col:
        _render_chat_panel(id_to_name)
    with right_col:
        _render_source_panel()


def _render_conversation_panel(id_to_name: dict[int, str]) -> None:
    """Render the left conversation history panel.

    Args:
        id_to_name: Mapping of document IDs to names.
    """
    st.markdown("##### 💬 Conversations")
    st.divider()

    # New chat button
    if st.button("➕ New Chat", use_container_width=True, key="new_chat"):
        new_id = str(uuid.uuid4())[:8]
        st.session_state["chat_session"] = new_id
        st.session_state["chat_messages"] = []
        st.session_state["chat_sessions"][new_id] = {
            "title": f"Chat {new_id[:4]}",
            "created": datetime.now().isoformat(),
            "document_id": st.session_state.get("chat_document_id"),
        }
        st.rerun()

    st.divider()

    # Recent PDFs
    st.markdown("##### 📚 Recent PDFs")
    for doc_id, doc_name in id_to_name.items():
        if st.button(f"📄 {doc_name[:25]}...", key=f"pd_{doc_id}", use_container_width=True):
            st.session_state["chat_document_id"] = doc_id
            notify_info(f"Switched to: {doc_name}")
            st.rerun()

    st.divider()

    # Conversation history
    st.markdown("##### 🗨️ History")
    sessions = st.session_state.get("chat_sessions", {})
    active_session = _get_active_session_id()

    for sid, sdata in sessions.items():
        is_active = sid == active_session
        title = sdata.get("title", f"Chat {sid[:4]}")
        created = sdata.get("created", "")
        msg_count = 0
        for msg_key in ["chat_messages", f"chat_messages_{sid}"]:
            msgs = st.session_state.get(msg_key, [])
            if msgs:
                msg_count = len(msgs)

        render_conversation_item(
            session_id=sid,
            title=title,
            date=created[:10] if created else "",
            is_active=is_active,
            message_count=msg_count,
        )


def _render_chat_panel(id_to_name: dict[int, str]) -> None:
    """Render the center chat conversation panel.

    Args:
        id_to_name: Mapping of document IDs to names.
    """
    # Chat header
    doc_id = st.session_state.get("chat_document_id")
    doc_name = id_to_name.get(doc_id, "No document selected")

    header_cols = st.columns([2, 1, 1, 1, 1])
    with header_cols[0]:
        st.markdown(f"**📄 {doc_name[:30]}**" if doc_name != "No document selected" else "**💬 AI Chat**")
    with header_cols[1]:
        st.markdown("<span class='neuro-badge'>🤖 llama3.2</span>", unsafe_allow_html=True)
    with header_cols[2]:
        st.markdown("<span class='neuro-badge'>🔒 Offline</span>", unsafe_allow_html=True)

    with header_cols[3]:
        if st.button("🆕", help="New Chat", key="new_inline"):
            new_id = str(uuid.uuid4())[:8]
            st.session_state["chat_session"] = new_id
            st.session_state["chat_messages"] = []
            st.rerun()
    with header_cols[4]:
        if st.button("🗑️", help="Clear Chat", key="clear_chat"):
            st.session_state["chat_messages"] = []
            st.rerun()

    st.divider()

    # Display messages
    messages = st.session_state.get("chat_messages", [])

    if not messages:
        st.markdown(
            """
            <div class="neuro-empty">
                <div class="neuro-empty-icon">💬</div>
                <div class="neuro-empty-title">Ask anything about your PDF</div>
                <p style="color:#6B7280;">Questions, concepts, examples - I'll help you learn.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    for i, msg in enumerate(messages):
        render_chat_message(
            role=msg.get("role", "user"),
            content=msg.get("content", ""),
            sources=msg.get("sources"),
            confidence=msg.get("confidence", 0),
            followups=msg.get("followups"),
            related_topics=msg.get("related_topics"),
            message_id=str(i),
        )

    # Handle pending question
    pending = st.session_state.pop("pending_question", None)
    if pending:
        _send_message(pending, doc_id)

    # Chat input
    question = render_chat_input()
    if question:
        _send_message(question, doc_id)


def _send_message(question: str, doc_id: int | None) -> None:
    """Process and send a chat message.

    Args:
        question: User question text.
        doc_id: Optional document ID to scope the question.
    """
    messages = st.session_state.get("chat_messages", [])

    # Add user message
    messages.append({"role": "user", "content": question})
    st.session_state["chat_messages"] = messages

    # Show loading
    with st.chat_message("assistant"):
        with st.spinner(""):
            response_placeholder = st.empty()

            try:
                response_placeholder.markdown("🔍 Searching notes...")
                doc_ids = [doc_id] if doc_id else None
                result = answer_question(question, document_ids=doc_ids)

                response_placeholder.markdown("✨ Generating response...")

                answer = result.get("answer", "No answer available.")
                sources = result.get("sources", [])
                confidence = result.get("confidence", 0)
                related_topics = result.get("related_topics", [])
                followups = result.get("suggested_followups", [])

                # Add assistant message
                messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                        "sources": sources,
                        "confidence": confidence,
                        "related_topics": related_topics,
                        "followups": followups,
                    }
                )
                st.session_state["chat_messages"] = messages

                response_placeholder.empty()
                st.rerun()

            except Exception as exc:
                notify_error(f"Failed to get answer: {exc}")
                response_placeholder.empty()

                messages.append(
                    {
                        "role": "assistant",
                        "content": "Sorry, I encountered an error. Please try again.",
                        "sources": [],
                        "confidence": 0,
                        "related_topics": [],
                        "followups": [],
                    }
                )
                st.session_state["chat_messages"] = messages
                st.rerun()


def _render_source_panel() -> None:
    """Render the right source viewer panel."""
    st.markdown("##### 📚 Source Viewer")
    st.divider()

    messages = st.session_state.get("chat_messages", [])
    last_sources = []
    for msg in reversed(messages):
        if msg.get("role") == "assistant" and msg.get("sources"):
            last_sources = msg["sources"]
            break

    if last_sources:
        for source in last_sources[:5]:
            from components.pdf_viewer import render_source_citation

            render_source_citation(source)
            st.divider()
    else:
        st.markdown(
            """
            <div class="neuro-empty">
                <div class="neuro-empty-icon">📖</div>
                <div class="neuro-empty-title">No Sources Yet</div>
                <p style="color:#6B7280;">Sources will appear here after asking a question.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    render_ai_chat()
