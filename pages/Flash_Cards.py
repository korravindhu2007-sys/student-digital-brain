"""Flash Cards page for NeuroNote."""

from __future__ import annotations

import random
from typing import Any

import streamlit as st

from components.cards import stat_card
from components.empty_state import render_empty_state
from components.notifications import notify_info, notify_success
from components.topbar import render_topbar
from services.backend import get_pdf_options
from styles.custom_css import inject_custom_css


def _get_sample_cards(doc: dict[str, Any]) -> list[dict[str, Any]]:
    """Generate sample flash cards from document.

    Args:
        doc: Document dict.

    Returns:
        List of flash card dicts with front/back.
    """
    subject = doc.get("subject", "General")
    topic = doc.get("topic", "General")

    sample_cards = [
        {
            "front": f"What is the main topic of {topic}?",
            "back": f"The main topic covers key concepts in {subject} related to {topic}.",
            "category": "Definitions",
            "difficulty": "Easy",
        },
        {
            "front": f"Explain the importance of {topic} in {subject}.",
            "back": f"{topic} is fundamental to understanding {subject}. It provides the foundation for advanced concepts.",
            "category": "Concepts",
            "difficulty": "Medium",
        },
        {
            "front": f"What are the key applications of {topic}?",
            "back": f"Applications include real-world implementations and theoretical frameworks in {subject}.",
            "category": "Examples",
            "difficulty": "Medium",
        },
        {
            "front": f"List the main components related to {topic}.",
            "back": f"The components include definitions, principles, methodologies, and practical applications within {subject}.",
            "category": "Definitions",
            "difficulty": "Easy",
        },
        {
            "front": f"Describe how {topic} relates to other concepts in {subject}.",
            "back": f"{topic} is interconnected with various other topics in {subject}, forming a comprehensive knowledge framework.",
            "category": "Concepts",
            "difficulty": "Hard",
        },
        {
            "front": f"What formulas or equations are used in {topic}?",
            "back": f"Formulas in {topic} typically involve mathematical relationships that describe the underlying principles.",
            "category": "Formulae",
            "difficulty": "Hard",
        },
    ]
    return sample_cards


def _init_card_state() -> None:
    """Initialize flash card session state."""
    if "card_index" not in st.session_state:
        st.session_state["card_index"] = 0
    if "card_flipped" not in st.session_state:
        st.session_state["card_flipped"] = False
    if "card_learned" not in st.session_state:
        st.session_state["card_learned"] = set()
    if "card_review" not in st.session_state:
        st.session_state["card_review"] = set()
    if "card_shuffled" not in st.session_state:
        st.session_state["card_shuffled"] = False


def render_flash_cards() -> None:
    """Render the Flash Cards page."""
    inject_custom_css()
    render_topbar(title="🃏 Flash Cards")
    _init_card_state()

    try:
        options = get_pdf_options()
        documents = options.get("documents", [])
    except Exception:
        documents = []

    if not documents:
        if render_empty_state(
            "No Flash Cards Generated",
            "Upload a PDF to generate flash cards.",
            icon="🃏",
            action_label="📤 Upload PDF",
            action_key="go_upload_cards",
        ):
            st.session_state["page"] = "Upload"
            st.rerun()
        return

    # Document selector
    doc_names = {
        f"{d.get('source_name') or d.get('filename', 'Unknown')} - {d.get('subject', 'General')}": d for d in documents
    }
    selected_doc_name = st.selectbox(
        "Select Document",
        list(doc_names.keys()),
        key="cards_doc_selector",
    )
    doc = doc_names[selected_doc_name]
    cards = _get_sample_cards(doc)
    total_cards = len(cards)

    if "card_data" not in st.session_state or st.session_state.get("cards_doc") != selected_doc_name:
        st.session_state["card_data"] = cards
        st.session_state["card_index"] = 0
        st.session_state["card_flipped"] = False
        st.session_state["card_shuffled"] = False
        st.session_state["cards_doc"] = selected_doc_name

    cards = st.session_state["card_data"]
    total_cards = len(cards)
    card_index = st.session_state["card_index"]
    flipped = st.session_state["card_flipped"]

    # Progress bar
    learned_count = len(st.session_state["card_learned"])
    progress = (card_index + 1) / total_cards if total_cards > 0 else 0
    st.progress(progress, text=f"Card {card_index + 1} of {total_cards}")

    # Stats row
    cols = st.columns(4)
    with cols[0]:
        stat_card("Cards Completed", str(learned_count), "✅")
    with cols[1]:
        stat_card("Remaining", str(total_cards - learned_count), "📝")
    with cols[2]:
        accuracy = int((learned_count / max(card_index, 1)) * 100) if card_index > 0 else 0
        stat_card("Accuracy", f"{accuracy}%", "🎯")
    with cols[3]:
        stat_card("Bookmarks", str(len(st.session_state["card_review"])), "🔖")

    st.divider()

    # Flash card display
    if card_index < total_cards:
        card = cards[card_index]
        _render_card(card, flipped, card_index, total_cards)
    else:
        _render_completion()


def _render_card(card: dict[str, Any], flipped: bool, card_index: int, total_cards: int) -> None:
    """Render a single flash card.

    Args:
        card: Card dict with front/back.
        flipped: Whether card is flipped.
        card_index: Current card index.
        total_cards: Total number of cards.
    """
    # Card display
    card_html = f"""
    <div class="neuro-flash-card" onclick="flipCard()">
        <div class="neuro-flash-card-front">
            {card["front"]}
        </div>
    </div>
    """

    if flipped:
        card_html = f"""
        <div class="neuro-flash-card">
            <div class="neuro-flash-card-back">
                {card["back"]}
            </div>
            <div style="margin-top:1rem; display:flex; gap:0.5rem;">
                <span class="neuro-badge">{card.get("category", "General")}</span>
                <span class="neuro-badge">{card.get("difficulty", "Medium")}</span>
            </div>
        </div>
        """

    st.markdown(card_html, unsafe_allow_html=True)

    # Buttons
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("🔄 Flip", key="flip_btn", use_container_width=True):
            st.session_state["card_flipped"] = not flipped
            st.rerun()

    with col2:
        prev_disabled = card_index <= 0
        if st.button("⬅️ Previous", key="prev_btn", use_container_width=True, disabled=prev_disabled):
            st.session_state["card_index"] = max(0, card_index - 1)
            st.session_state["card_flipped"] = False
            st.rerun()

    with col3:
        next_disabled = card_index >= total_cards - 1
        if st.button("Next ➡️", key="next_btn", use_container_width=True, disabled=next_disabled):
            st.session_state["card_index"] = min(total_cards - 1, card_index + 1)
            st.session_state["card_flipped"] = False
            st.rerun()

    with col4:
        if st.button("🔀 Shuffle", key="shuffle_btn", use_container_width=True):
            random.shuffle(st.session_state["card_data"])
            st.session_state["card_index"] = 0
            st.session_state["card_flipped"] = False
            st.session_state["card_shuffled"] = True
            st.rerun()

    # Action buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("✅ Mark Learned", key="learned_btn", use_container_width=True):
            st.session_state["card_learned"].add(card_index)
            notify_success("Marked as learned!")
            if card_index < total_cards - 1:
                st.session_state["card_index"] = card_index + 1
                st.session_state["card_flipped"] = False
                st.rerun()
    with col2:
        if st.button("🔖 Review Later", key="review_btn", use_container_width=True):
            st.session_state["card_review"].add(card_index)
            notify_info("Added to review list")
    with col3:
        if st.button("🎲 Random", key="random_btn", use_container_width=True):
            st.session_state["card_index"] = random.randint(0, total_cards - 1)
            st.session_state["card_flipped"] = False
            st.rerun()


def _render_completion() -> None:
    """Render the completion state when all cards are done."""
    st.markdown(
        """
        <div class="neuro-empty">
            <div class="neuro-empty-icon">🎉</div>
            <div class="neuro-empty-title">All Cards Reviewed!</div>
            <p style="color:#6B7280; margin-bottom:1.5rem;">
                Great job! You've gone through all the flash cards.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("🔄 Start Over", type="primary", use_container_width=True):
        st.session_state["card_index"] = 0
        st.session_state["card_flipped"] = False
        st.session_state["card_learned"] = set()
        st.session_state["card_review"] = set()
        st.rerun()


if __name__ == "__main__":
    render_flash_cards()
