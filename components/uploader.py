from __future__ import annotations

from typing import Iterable

import streamlit as st

from components.cards import backend_response_panel
from components.notifications import notify_error, notify_success
from components.progress import render_processing_progress


def render_upload_panel(
    title: str,
    help_text: str,
    accepted_types: Iterable[str],
    upload_kind: str,
    processor,
    max_files: int = 10,
) -> None:
    key_prefix = upload_kind.lower().replace(" ", "-")
    st.subheader(title)
    st.caption(help_text)

    files = st.file_uploader(
        "Drop files here",
        type=list(accepted_types),
        accept_multiple_files=True,
        help=f"Up to {max_files} files can be selected in this frontend.",
        key=f"{key_prefix}-files",
    )

    subject = st.text_input("Subject", placeholder="Example: Biology, Physics, History", key=f"{key_prefix}-subject")
    topic = st.text_input(
        "Topic", placeholder="Example: Chapter 3, Mechanics, Cell structure", key=f"{key_prefix}-topic"
    )
    notes = st.text_area(
        "Notes",
        placeholder="Optional context for the backend processing step.",
        height=90,
        key=f"{key_prefix}-notes",
    )

    disabled = not files
    if st.button("Upload and process", type="primary", disabled=disabled, key=f"{key_prefix}-submit"):
        if len(files) > max_files:
            notify_error(f"Select {max_files} files or fewer.")
            return

        progress_slot = st.empty()
        with progress_slot:
            render_processing_progress(0, "Preparing upload")
        with st.spinner("Sending files to the local processing queue..."):
            results = []
            for index, file in enumerate(files, start=1):
                with progress_slot:
                    render_processing_progress(int(index / len(files) * 100), f"Processing {file.name}")
                try:
                    results.append(
                        processor(
                            file=file,
                            metadata={
                                "kind": upload_kind,
                                "subject": subject,
                                "topic": topic,
                                "notes": notes,
                            },
                        )
                    )
                except Exception as exc:
                    results.append(
                        {
                            "ok": False,
                            "file_name": file.name,
                            "status": "failed",
                            "error": str(exc),
                        }
                    )

        failed = [result for result in results if not result.get("ok", False)]
        if failed:
            notify_error(f"{len(failed)} upload item failed.")
        else:
            notify_success(f"Queued {len(results)} {upload_kind} item(s) for backend processing.")
        _render_extraction_summary(results)
        backend_response_panel(f"{title} backend responses", results)


def _render_extraction_summary(results: list[dict[str, object]]) -> None:
    for result in results:
        if not result.get("ok", False):
            continue
        source_name = result.get("source_name", "Uploaded file")
        extracted_chars = int(result.get("extracted_chars") or 0)
        page_count = int(result.get("page_count") or 0)
        image_count = int(result.get("image_count") or 0)
        if extracted_chars > 0:
            st.success(
                f"{source_name}: extracted {extracted_chars:,} characters"
                + (f" from {page_count} page(s)" if page_count else "")
                + (f" and found {image_count} image(s)" if image_count else "")
                + "."
            )
        else:
            st.warning(f"{source_name}: no readable text was extracted. This PDF may need OCR or may be image-only.")
