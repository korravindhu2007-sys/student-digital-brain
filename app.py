"""NeuroNote - Offline AI Study Companion."""

from __future__ import annotations

import sys
from pathlib import Path

# ruff: noqa: E402

# Ensure both root and src are in path for imports
ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import streamlit as st

from components.sidebar import render_sidebar
from pages.dashboard import render_dashboard
from pages.AI_Chat import render_ai_chat
from pages.Flash_Cards import render_flash_cards
from pages.study_mode import render_study_mode
from pages.upload import render_upload

PAGE_REGISTRY = {
    "Dashboard": render_dashboard,
    "Upload": render_upload,
    "AI Chat": render_ai_chat,
    "Flash Cards": render_flash_cards,
    "Study Mode": render_study_mode,
}


def configure_page() -> None:
    """Configure the Streamlit page settings."""
    st.set_page_config(
        page_title="NeuroNote - Offline AI Study Companion",
        page_icon="🧠",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def init_app_state() -> None:
    """Initialize application session state."""
    if "page" not in st.session_state:
        st.session_state["page"] = "Dashboard"
    if "theme" not in st.session_state:
        st.session_state["theme"] = "dark"
    if "ollama_model" not in st.session_state:
        st.session_state["ollama_model"] = "llama3.2"
    if "database_path" not in st.session_state:
        st.session_state["database_path"] = "database/neuronote.db"
    if "chat_messages" not in st.session_state:
        st.session_state["chat_messages"] = []
    if "chat_sessions" not in st.session_state:
        st.session_state["chat_sessions"] = {}
    if "chat_session" not in st.session_state:
        st.session_state["chat_session"] = "default"


def main() -> None:
    """Main application entry point."""
    configure_page()
    init_app_state()

    # Render sidebar and get selected page
    selected_page = render_sidebar()

    # Render the selected page
    if selected_page in PAGE_REGISTRY:
        PAGE_REGISTRY[selected_page]()
    else:
        render_dashboard()


if __name__ == "__main__":
    main()
