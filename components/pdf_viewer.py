"""PDF viewer component for NeuroNote."""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Any

import streamlit as st


def render_pdf_preview(
    file_path: str | Path,
    page_number: int | None = None,
    height: int = 600,
) -> None:
    """Render an embedded PDF preview.

    Args:
        file_path: Path to the PDF file.
        page_number: Optional page to highlight.
        height: Viewer height in pixels.
    """
    file_path = Path(file_path).resolve()
    if not file_path.exists():
        st.error("PDF file not found.")
        return

    with open(file_path, "rb") as f:
        pdf_bytes = f.read()

    pdf_b64 = base64.b64encode(pdf_bytes).decode()
    pdf_display = f"""
        <div class="neuro-pdf-container">
            <iframe
                src="data:application/pdf;base64,{pdf_b64}#page={page_number or 1}"
                width="100%"
                height="{height}px"
                style="border:none;"
            ></iframe>
        </div>
    """
    st.markdown(pdf_display, unsafe_allow_html=True)


def render_source_citation(source: dict[str, Any]) -> None:
    """Render a source citation card.

    Args:
        source: Source dict with keys: source_filename, page_number,
                chunk_number, text, confidence.
    """
    filename = source.get("source_filename") or source.get("filename", "Unknown")
    page = source.get("page_number") or source.get("page", "?")
    chunk = source.get("chunk_number") or source.get("chunk_index", "?")
    text = source.get("text", "")[:300]
    confidence = source.get("confidence", 0)

    st.markdown(
        f"""
        <div class="neuro-source">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-weight:500;">📄 {filename}</span>
                <span class="neuro-badge">Page {page}</span>
            </div>
            <div style="margin-top:0.5rem; font-size:0.9rem; color:#6B7280;">
                {text}{"..." if len(source.get("text", "")) > 300 else ""}
            </div>
            <div style="display:flex; gap:0.5rem; margin-top:0.5rem;">
                <span class="neuro-badge">Chunk {chunk}</span>
                <span class="neuro-badge">Confidence: {confidence}%</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_document_card(doc: dict[str, Any]) -> None:
    """Render a document info card.

    Args:
        doc: Document dict with keys: filename, pages, subject, topic, status, etc.
    """
    name = doc.get("source_name") or doc.get("filename", "Unknown")
    pages = doc.get("page_count") or doc.get("pages", 0)
    subject = doc.get("subject", "General")
    topic = doc.get("topic", "General")
    status = doc.get("status", "processed")

    status_colors = {
        "processed": "#10B981",
        "cached": "#F59E0B",
        "failed": "#EF4444",
        "processing": "#3B82F6",
    }
    status_color = status_colors.get(status, "#6B7280")

    st.markdown(
        f"""
        <div class="neuro-card">
            <div style="display:flex; justify-content:space-between; align-items:start;">
                <div>
                    <div style="font-weight:600; margin-bottom:0.25rem;">📄 {name}</div>
                    <div style="font-size:0.85rem; color:#6B7280;">
                        {subject} / {topic}
                    </div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:1.5rem; font-weight:700; color:#7C3AED;">{pages}</div>
                    <div style="font-size:0.75rem; color:#6B7280;">pages</div>
                </div>
            </div>
            <div style="margin-top:0.75rem; display:flex; gap:1rem;">
                <span style="color:{status_color}; font-size:0.85rem;">
                    &#9679; {status.title()}
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
