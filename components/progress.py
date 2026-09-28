from __future__ import annotations

import streamlit as st


def render_processing_progress(value: int, text: str) -> None:
    st.progress(max(0, min(100, value)), text=text)


def render_subject_progress(progress_rows: list[dict[str, object]]) -> None:
    if not progress_rows:
        st.info("Progress data will appear after the backend records study sessions.")
        return

    for row in progress_rows:
        subject = str(row["subject"])
        completion = int(row["completion"])
        st.write(f"**{subject}**")
        st.progress(completion, text=f"{completion}% ready")


def render_activity_table(rows: list[dict[str, object]]) -> None:
    if not rows:
        st.info("Recent activity will appear here after uploads and study sessions.")
        return

    for index, row in enumerate(rows, start=1):
        with st.container(border=True):
            cols = st.columns([1, 2, 1])
            cols[0].caption(str(row.get("Time", f"Item {index}")))
            cols[1].write(str(row.get("Activity", "Activity")))
            cols[2].success(str(row.get("Status", "Done")))
