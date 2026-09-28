from __future__ import annotations

import streamlit as st


def render_search_controls() -> dict[str, object]:
    cols = st.columns([1, 1, 1])
    subject = cols[0].text_input("Subject", placeholder="Biology")
    topic = cols[1].text_input("Topic", placeholder="Photosynthesis")
    keyword = cols[2].text_input("Keyword", placeholder="chlorophyll")

    filters = st.columns([1, 1])
    source_type = filters[0].selectbox("Source type", ["All types", "PDF", "Image", "Audio", "Text"])
    ranking = filters[1].selectbox("Ranking", ["Most relevant", "Newest", "Needs revision"])

    return {
        "subject": subject,
        "topic": topic,
        "keyword": keyword,
        "source_type": source_type,
        "ranking": ranking,
    }
