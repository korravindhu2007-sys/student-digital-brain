"""Status card component for NeuroNote."""

from __future__ import annotations

import streamlit as st


def render_status_card() -> None:
    """Render the floating status card showing system status."""
    dark = st.session_state.get("theme", "dark") == "dark"
    bg = "#1A1A23" if dark else "#FFFFFF"
    border = "#2A2A3A" if dark else "#E5E7EB"
    text = "#E8E8ED" if dark else "#1A1A2E"

    st.markdown(
        f"""
        <div style="
            background: {bg};
            border: 1px solid {border};
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 1rem;
        ">
            <div style="display:flex; align-items:center; gap:1rem; justify-content:space-around;">
                <div class='neuro-status'>
                    <span class='neuro-status-dot online'></span>
                    <span style="color:{text}; font-size:0.85rem;">Database Connected</span>
                </div>
                <div class='neuro-status'>
                    <span class='neuro-status-dot online'></span>
                    <span style="color:{text}; font-size:0.85rem;">Ollama Running</span>
                </div>
                <div class='neuro-status'>
                    <span class='neuro-status-dot online'></span>
                    <span style="color:{text}; font-size:0.85rem;">Offline Mode Enabled</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
