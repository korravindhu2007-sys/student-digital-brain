"""Loading state components for NeuroNote."""

from __future__ import annotations

import time
from typing import Any

import streamlit as st


def render_loading_skeleton(lines: int = 3) -> None:
    """Render a loading skeleton animation.

    Args:
        lines: Number of skeleton lines to show.
    """
    for _ in range(lines):
        st.markdown("<div class='neuro-skeleton' style='width:100%;'></div>", unsafe_allow_html=True)
        st.markdown(
            "<div class='neuro-skeleton' style='width:75%;'></div>",
            unsafe_allow_html=True,
        )
        st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)


def render_processing_stages(
    stages: list[dict[str, Any]],
    current_stage: int,
    start_time: float | None = None,
) -> None:
    """Render processing stages with progress indicators.

    Args:
        stages: List of stage dicts with 'label' and 'icon' keys.
        current_stage: Index of the current active stage.
        start_time: Optional start time for elapsed time display.
    """
    for i, stage in enumerate(stages):
        label = stage.get("label", f"Step {i + 1}")
        icon = stage.get("icon", "⏳")

        if i < current_stage:
            cls = "neuro-stage-complete"
            status_icon = "✅"
        elif i == current_stage:
            cls = "neuro-stage-active"
            status_icon = "🔄"
        else:
            cls = "neuro-stage-pending"
            status_icon = "⏳"

        st.markdown(
            f"<div class='neuro-stage {cls}'><span>{status_icon}</span><span>{icon} {label}</span></div>",
            unsafe_allow_html=True,
        )

    if start_time is not None:
        elapsed = time.time() - start_time
        st.caption(f"Elapsed: {elapsed:.1f}s")


def render_chat_loading() -> None:
    """Render the chat thinking animation."""
    st.markdown(
        """
        <div class="neuro-card" style="margin-right:2rem;">
            <div style="display:flex; align-items:center; gap:0.75rem;">
                <div style="display:flex; gap:0.25rem;">
                    <span style="
                        width:8px; height:8px; background:#7C3AED; border-radius:50%;
                        animation: bounce 1.4s ease-in-out infinite both;
                    "></span>
                    <span style="
                        width:8px; height:8px; background:#7C3AED; border-radius:50%;
                        animation: bounce 1.4s ease-in-out infinite both;
                        animation-delay: 0.16s;
                    "></span>
                    <span style="
                        width:8px; height:8px; background:#7C3AED; border-radius:50%;
                        animation: bounce 1.4s ease-in-out infinite both;
                        animation-delay: 0.32s;
                    "></span>
                </div>
                <span style="color:#6B7280; font-size:0.9rem;">Thinking...</span>
            </div>
        </div>
        <style>
            @keyframes bounce {
                0%, 80%, 100% { transform: scale(0); }
                40% { transform: scale(1); }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_searching_animation() -> None:
    """Render the searching animation for retrieval."""
    st.markdown(
        """
        <div class="neuro-card" style="margin-right:2rem;">
            <div style="display:flex; align-items:center; gap:0.75rem;">
                <span style="font-size:1.2rem;">🔍</span>
                <span style="color:#6B7280; font-size:0.9rem;">Searching notes...</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_generating_animation() -> None:
    """Render the generating response animation."""
    st.markdown(
        """
        <div class="neuro-card" style="margin-right:2rem;">
            <div style="display:flex; align-items:center; gap:0.75rem;">
                <span style="font-size:1.2rem;">✨</span>
                <span style="color:#6B7280; font-size:0.9rem;">Generating response...</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
