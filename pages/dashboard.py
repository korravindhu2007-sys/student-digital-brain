"""Dashboard page for NeuroNote."""

from __future__ import annotations

import streamlit as st

from components.cards import document_card, stat_card
from components.empty_state import render_welcome_state
from components.status_card import render_status_card
from components.topbar import render_topbar
from services.backend import get_dashboard_data, get_pdf_options
from styles.custom_css import inject_custom_css


def render_dashboard() -> None:
    """Render the modern dashboard page."""
    inject_custom_css()
    render_topbar(title="📊 Dashboard")

    try:
        data = get_dashboard_data()
        options = get_pdf_options()
        documents = options.get("documents", [])
    except Exception:
        data = {"metrics": {}, "counts": {}}
        documents = []

    counts = data.get("counts", {})

    # Stats Cards Row
    if documents:
        st.markdown("##### Overview")
        cols = st.columns(6)
        stat_items = [
            ("Uploaded Documents", str(counts.get("documents", len(documents))), "📄"),
            ("Pages Processed", str(sum(d.get("page_count", d.get("pages", 0)) for d in documents)), "📑"),
            ("Flash Cards", str(counts.get("flashcards", 0)), "🃏"),
            ("Study Sessions", str(counts.get("studies", 0)), "📖"),
            ("Chat Sessions", str(counts.get("chats", 0)), "💬"),
            ("Storage Used", f"{counts.get('storage_mb', 0):.1f}MB", "💾"),
        ]
        for col, (label, value, icon) in zip(cols, stat_items, strict=True):
            with col:
                stat_card(label, value, icon)
    else:
        render_welcome_state()
        return

    st.divider()

    # Quick Actions
    st.markdown("##### Quick Actions")
    cols = st.columns(4)
    with cols[0]:
        if st.button("📤 **Upload PDF**\n\nAdd new study material", key="qa_upload", use_container_width=True):
            st.session_state["page"] = "Upload"
            st.rerun()
    with cols[1]:
        if st.button("🤖 **AI Chat**\n\nAsk questions about your PDF", key="qa_chat", use_container_width=True):
            st.session_state["page"] = "AI Chat"
            st.rerun()
    with cols[2]:
        if st.button("📖 **Study Notes**\n\nReview study material", key="qa_study", use_container_width=True):
            st.session_state["page"] = "Study Mode"
            st.rerun()
    with cols[3]:
        if st.button("🃏 **Flash Cards**\n\nTest your knowledge", key="qa_cards", use_container_width=True):
            st.session_state["page"] = "Flash Cards"
            st.rerun()

    st.divider()

    # Recent Documents
    st.markdown("##### Recent Documents")
    for doc in documents[:5]:
        document_card(doc)

    # Status Card
    st.divider()
    render_status_card()


if __name__ == "__main__":
    render_dashboard()
