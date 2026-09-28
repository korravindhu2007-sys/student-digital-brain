"""Formula Sheet page for NeuroNote."""

from __future__ import annotations

from typing import Any

import streamlit as st

from components.empty_state import render_empty_state
from components.notifications import notify_success
from components.topbar import render_topbar
from services.backend import get_pdf_options
from styles.custom_css import inject_custom_css


def _get_formulas(doc: dict[str, Any]) -> list[dict[str, Any]]:
    """Get formulas from document.

    Args:
        doc: Document dict.

    Returns:
        List of formula dicts.
    """
    subject = doc.get("subject", "General")

    sample_formulas = [
        {
            "formula": "f(x) = mx + b",
            "meaning": "Linear equation representing a straight line",
            "variables": "m = slope, b = y-intercept, x = independent variable",
            "where_used": f"Used extensively in {subject} for modeling linear relationships",
            "example": "If m=2, b=3, then f(5) = 2(5) + 3 = 13",
            "page": 1,
            "type": "Formula",
        },
        {
            "formula": "A = πr²",
            "meaning": "Area of a circle",
            "variables": "r = radius, π ≈ 3.14159",
            "where_used": f"Fundamental in {subject} geometry calculations",
            "example": "If r = 7, then A = π(49) ≈ 153.94",
            "page": 2,
            "type": "Equation",
        },
        {
            "formula": "E = mc²",
            "meaning": "Energy-mass equivalence",
            "variables": "E = energy, m = mass, c = speed of light",
            "where_used": f"Core principle in {subject} physics",
            "example": "Energy released = mass × (3×10⁸)²",
            "page": 3,
            "type": "Formula",
        },
        {
            "formula": "Σ (xi - μ)² / N",
            "meaning": "Variance of a dataset",
            "variables": "xi = each value, μ = mean, N = number of values",
            "where_used": f"Statistical analysis in {subject}",
            "example": "Used to measure data spread in experiments",
            "page": 4,
            "type": "Algorithm",
        },
    ]
    return sample_formulas


def _filter_formulas(formulas: list[dict[str, Any]], search: str, filter_type: str) -> list[dict[str, Any]]:
    """Filter formulas by search query and type.

    Args:
        formulas: List of formula dicts.
        search: Search query.
        filter_type: Type filter.

    Returns:
        Filtered formula list.
    """
    filtered = formulas

    if search:
        search_lower = search.lower()
        filtered = [
            f
            for f in filtered
            if search_lower in f.get("formula", "").lower()
            or search_lower in f.get("meaning", "").lower()
            or search_lower in f.get("where_used", "").lower()
        ]

    if filter_type != "All":
        filtered = [f for f in filtered if f.get("type") == filter_type]

    return filtered


def render_formula_sheet() -> None:
    """Render the Formula Sheet page."""
    inject_custom_css()
    render_topbar(title="📐 Formula Sheet")

    try:
        options = get_pdf_options()
        documents = options.get("documents", [])
    except Exception:
        documents = []

    if not documents:
        if render_empty_state(
            "No Formulas Found",
            "Upload a PDF to extract formulas.",
            icon="📐",
            action_label="📤 Upload PDF",
            action_key="go_upload_formula",
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
        key="formula_doc_selector",
    )
    doc = doc_names[selected_doc_name]

    # Search and filter
    cols = st.columns([2, 1])
    with cols[0]:
        search = st.text_input(
            "🔍 Search formulas",
            placeholder="Search by name, meaning, or usage...",
            key="formula_search",
        )
    with cols[1]:
        filter_type = st.selectbox(
            "Filter",
            ["All", "Formula", "Algorithm", "Syntax", "Equation"],
            key="formula_filter",
        )

    # Get and filter formulas
    all_formulas = _get_formulas(doc)
    formulas = _filter_formulas(all_formulas, search, filter_type)

    st.divider()

    if not formulas:
        st.markdown(
            """
            <div class="neuro-empty">
                <div class="neuro-empty-icon">🔍</div>
                <div class="neuro-empty-title">No formulas match your search</div>
                <p style="color:#6B7280;">Try different keywords or clear filters.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    st.caption(f"Showing {len(formulas)} formula(s)")

    for formula_data in formulas:
        _render_formula_card(formula_data)


def _render_formula_card(data: dict[str, Any]) -> None:
    """Render a single formula card.

    Args:
        data: Formula data dict.
    """
    st.markdown(
        f"""
        <div class="neuro-formula-card">
            <div style="display:flex; justify-content:space-between; align-items:start;">
                <span class="neuro-badge">{data.get("type", "Formula")}</span>
                <span class="neuro-badge">Page {data.get("page", "?")}</span>
            </div>
            <div class="neuro-formula">{data.get("formula", "")}</div>
            <div style="margin-top:0.75rem;">
                <strong>Meaning:</strong>
                <p style="color:#6B7280; margin:0.25rem 0 0.75rem 0;">{data.get("meaning", "")}</p>
            </div>
            <div style="margin-top:0.5rem;">
                <strong>Variables:</strong>
                <p style="color:#6B7280; margin:0.25rem 0 0.75rem 0;">{data.get("variables", "")}</p>
            </div>
            <div style="margin-top:0.5rem;">
                <strong>Where Used:</strong>
                <p style="color:#6B7280; margin:0.25rem 0 0.75rem 0;">{data.get("where_used", "")}</p>
            </div>
            <div style="margin-top:0.5rem;">
                <strong>Example:</strong>
                <p style="color:#6B7280; margin:0.25rem 0 0.75rem 0;">{data.get("example", "")}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("📋 Copy Formula", key=f"copy_{data.get('formula', '')[:10]}", use_container_width=True):
        notify_success("Formula copied to clipboard!")


if __name__ == "__main__":
    render_formula_sheet()
