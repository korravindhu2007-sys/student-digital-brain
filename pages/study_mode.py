"""Study Mode page for NeuroNote."""

from __future__ import annotations

from typing import Any

import streamlit as st

from components.cards import topic_card
from components.empty_state import render_empty_state
from components.notifications import notify_info
from components.topbar import render_topbar
from services.backend import get_pdf_options
from styles.custom_css import inject_custom_css


def _get_study_content() -> list[dict[str, Any]]:
    """Get study content sections from backend.

    Returns:
        List of topic sections.
    """
    try:
        options = get_pdf_options()
        documents = options.get("documents", [])
        if not documents:
            return []

        sections = [
            {"title": "Introduction", "icon": "📌", "content": "Overview of the study material..."},
            {"title": "Key Definitions", "icon": "📚", "content": "Important terms and definitions..."},
            {"title": "Core Concepts", "icon": "🧠", "content": "Main concepts explained..."},
            {"title": "Examples", "icon": "💡", "content": "Practical examples and applications..."},
            {"title": "Summary", "icon": "📝", "content": "Chapter summary and key takeaways..."},
        ]
        return sections
    except Exception:
        return []


def render_study_mode() -> None:
    """Render the Study Mode page with TOC sidebar and expandable notes."""
    inject_custom_css()
    render_topbar(title="📖 Study Mode")

    try:
        options = get_pdf_options()
        documents = options.get("documents", [])
    except Exception:
        documents = []

    if not documents:
        if render_empty_state(
            "No Study Material Available",
            "Upload a PDF to start studying.",
            icon="📖",
            action_label="📤 Upload PDF",
            action_key="go_upload_study",
        ):
            st.session_state["page"] = "Upload"
            st.rerun()
        return

    # Select document to study
    doc_names = {
        f"{d.get('source_name') or d.get('filename', 'Unknown')} - {d.get('subject', 'General')}": d for d in documents
    }
    selected_doc_name = st.selectbox(
        "Select Document",
        list(doc_names.keys()),
        key="study_doc_selector",
    )
    doc = doc_names[selected_doc_name]

    # Three-column layout
    left_col, center_col, right_col = st.columns([1, 2.5, 1])

    with left_col:
        _render_table_of_contents()

    with center_col:
        _render_study_notes(doc)

    with right_col:
        _render_quick_actions(doc)


def _render_table_of_contents() -> None:
    """Render the table of contents sidebar."""
    st.markdown("##### 📑 Table of Contents")
    st.divider()

    sections = [
        ("📌", "Introduction"),
        ("📚", "Definitions"),
        ("🧠", "Concepts"),
        ("💡", "Examples"),
        ("📝", "Summary"),
    ]

    for icon, title in sections:
        if st.button(f"{icon} {title}", key=f"toc_{title}", use_container_width=True):
            notify_info(f"Jumping to {title}")


def _render_study_notes(doc: dict[str, Any]) -> None:
    """Render the main study notes content.

    Args:
        doc: Document dict.
    """
    st.markdown(f"##### 📖 Study Notes: {doc.get('source_name') or doc.get('filename', 'Unknown')}")
    st.caption(f"{doc.get('subject', 'General')} / {doc.get('topic', 'General')}")
    st.divider()

    sections = _get_study_content()

    for section in sections:
        _render_section(section)


def _render_section(section: dict[str, Any]) -> None:
    """Render a study section with actions.

    Args:
        section: Section dict with title, icon, content.
    """
    topic_card(
        title=section["title"],
        content=section["content"],
        icon=section["icon"],
    )


def _render_quick_actions(doc: dict[str, Any]) -> None:
    """Render quick actions sidebar.

    Args:
        doc: Document dict.
    """
    st.markdown("##### ⚡ Quick Actions")
    st.divider()

    if st.button("🤖 Ask AI", key="action_ask_ai", use_container_width=True):
        doc_id = doc.get("id") or doc.get("document_id")
        if doc_id:
            st.session_state["chat_document_id"] = doc_id
        st.session_state["page"] = "AI Chat"
        st.rerun()

    if st.button("🔖 Bookmark", key="action_bookmark", use_container_width=True):
        notify_info("Bookmarked!")

    if st.button("📄 Open Source PDF", key="action_source", use_container_width=True):
        notify_info("Opening PDF viewer...")

    st.divider()
    st.markdown("##### 📚 Related Topics")
    topics = [
        "Key Concepts",
        "Important Terms",
        "Practice Questions",
    ]
    for topic in topics:
        if st.button(topic, key=f"related_{topic}", use_container_width=True):
            notify_info(f"Loading {topic}...")


if __name__ == "__main__":
    render_study_mode()
