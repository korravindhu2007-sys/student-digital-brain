"""Upload page for NeuroNote."""

from __future__ import annotations

import time
from typing import Any

import streamlit as st

from components.notifications import notify_error, notify_success
from components.topbar import render_topbar
from components.upload_widget import render_upload_area, render_upload_result
from services.backend import process_document
from styles.custom_css import inject_custom_css

PROCESSING_STAGES = [
    {"label": "Uploading", "icon": "📤"},
    {"label": "Extracting", "icon": "📑"},
    {"label": "OCR", "icon": "🔍"},
    {"label": "Chunking", "icon": "🧩"},
    {"label": "Saving", "icon": "💾"},
    {"label": "Ready", "icon": "✅"},
]


def render_upload() -> None:
    """Render the modern upload page."""
    inject_custom_css()
    render_topbar(title="📤 Upload Study Material")

    file, subject, topic = render_upload_area()

    can_process = file is not None and subject and topic

    if not can_process:
        st.info("📝 Enter a subject and topic, then upload a PDF to get started.")
        return

    if st.button("🚀 Upload and Process", type="primary", use_container_width=True, disabled=not can_process):
        _process_file(file, subject, topic)


def _process_file(file: Any, subject: str, topic: str) -> None:
    """Process the uploaded file with progress stages.

    Args:
        file: Uploaded file object.
        subject: Subject name.
        topic: Topic name.
    """
    progress_placeholder = st.empty()
    start_time = time.time()

    try:
        # Stage 1: Uploading
        with progress_placeholder.container():
            _render_stage(0, start_time)
        time.sleep(0.3)

        # Stage 2-5: Processing
        with progress_placeholder.container():
            _render_stage(1, start_time)

        with st.spinner("Processing document..."):
            result = process_document(
                file=file,
                metadata={"subject": subject, "topic": topic},
            )

        if not result.get("ok"):
            notify_error(str(result.get("error", "Processing failed.")))
            progress_placeholder.empty()
            return

        # Stage 6: Ready
        with progress_placeholder.container():
            _render_stage(5, start_time)

        notify_success(f"Document processed! Created {result.get('chunk_count', 0)} chunks.")
        progress_placeholder.empty()

        # Show result
        render_upload_result(result)

    except Exception as exc:
        notify_error(str(exc))
        progress_placeholder.empty()


def _render_stage(stage_index: int, start_time: float) -> None:
    """Render a processing stage.

    Args:
        stage_index: Current stage index.
        start_time: Processing start time.
    """
    from components.loading import render_processing_stages

    render_processing_stages(PROCESSING_STAGES, stage_index, start_time=start_time)


if __name__ == "__main__":
    render_upload()
