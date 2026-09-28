"""Upload widget component for NeuroNote."""

from __future__ import annotations

from typing import Any

import streamlit as st


def render_upload_area() -> tuple[Any, str, str]:
    """Render the drag-and-drop upload area with metadata inputs.

    Returns:
        Tuple of (uploaded_file, subject, topic).
    """
    st.markdown("<div class='neuro-card'>", unsafe_allow_html=True)
    st.markdown("##### 📤 Upload Study Material")
    st.caption("Supported formats: PDF, PNG, JPG, JPEG (Max: 200MB)")

    file = st.file_uploader(
        "Choose a file",
        type=["pdf", "png", "jpg", "jpeg"],
        accept_multiple_files=False,
        key="upload_widget",
        label_visibility="collapsed",
    )

    col1, col2 = st.columns(2)
    with col1:
        subject = st.text_input(
            "Subject",
            placeholder="e.g., Biology, Mathematics",
            key="upload_subject",
        )
    with col2:
        topic = st.text_input(
            "Topic / Chapter",
            placeholder="e.g., Unit 1 - Cell Biology",
            key="upload_topic",
        )

    st.markdown("</div>", unsafe_allow_html=True)

    return file, subject.strip(), topic.strip()


def render_upload_progress(
    stages: list[dict[str, Any]],
    current_stage: int,
    start_time: float | None = None,
) -> None:
    """Render the upload processing progress.

    Args:
        stages: List of stage dicts with 'label' and 'icon'.
        current_stage: Current active stage index.
        start_time: Optional start time for elapsed time display.
    """
    from components.loading import render_processing_stages

    render_processing_stages(stages, current_stage, start_time=start_time)


def render_upload_result(result: dict[str, Any]) -> None:
    """Render the upload result summary.

    Args:
        result: Processing result dict.
    """
    if not result.get("ok"):
        st.error(f"❌ {result.get('error', 'Processing failed.')}")
        return

    st.markdown("<div class='neuro-card'>", unsafe_allow_html=True)
    st.markdown("##### ✅ Processing Complete")

    cols = st.columns(4)
    with cols[0]:
        st.metric("Pages", result.get("page_count", 0))
    with cols[1]:
        st.metric("Chunks", result.get("chunk_count", 0))
    with cols[2]:
        chars = result.get("extracted_chars", 0)
        st.metric("Characters", f"{chars:,}" if chars else "0")
    with cols[3]:
        status = "Cached" if result.get("cache_hit") else "New"
        st.metric("Status", status)

    st.markdown("</div>", unsafe_allow_html=True)

    cols = st.columns(2)
    with cols[0]:
        if st.button("🤖 Open AI Chat", key="open_chat_after_upload", use_container_width=True):
            st.session_state["page"] = "AI Chat"
            st.rerun()
    with cols[1]:
        if st.button("📖 Open Study Mode", key="open_study_after_upload", use_container_width=True):
            st.session_state["page"] = "Study Mode"
            st.rerun()
