"""Modern notification components for NeuroNote."""

from __future__ import annotations

import streamlit as st


def notify_success(message: str) -> None:
    """Show a success notification."""
    st.toast(f"✅ {message}", icon="✅")


def notify_error(message: str) -> None:
    """Show an error notification."""
    st.toast(f"❌ {message}", icon="❌")


def notify_warning(message: str) -> None:
    """Show a warning notification."""
    st.toast(f"⚠️ {message}", icon="⚠️")


def notify_info(message: str) -> None:
    """Show an info notification."""
    st.toast(f"ℹ️ {message}", icon="ℹ️")
