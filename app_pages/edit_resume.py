"""Generate and download an AI-edited resume."""

from __future__ import annotations

import streamlit as st

from src.db import repositories as repo
from src.services.resume_editor import build_exports, generate_edited_resume
from src.ui.session import ensure_session_defaults, page_header, require_config

ensure_session_defaults()
require_config()
page_header(
    "Edit resume",
    "Rewrite for the target JD without inventing experience. Download PDF or DOCX.",
    icon=":material/edit_note:",
)

if not st.session_state.analysis_id:
    st.warning(
        "Run an analysis first, then come back to generate a tailored rewrite.",
        icon=":material/warning:",
        title="Analysis required",
    )
    if st.button("Go to upload", type="primary", icon=":material/upload_file:"):
        st.switch_page("app_pages/upload.py")
    st.stop()

existing = repo.get_latest_resume_edit(st.session_state.analysis_id)
if existing:
    st.caption(f"Latest edit saved at {existing.get('created_at')}")

toolbar = st.container(horizontal=True, gap="small", vertical_alignment="center")
with toolbar:
    generate = st.button(
        "Generate AI rewrite",
        type="primary",
        icon=":material/auto_awesome:",
    )
    if existing:
        st.badge("Rewrite available", icon=":material/check:", color="green")

if generate:
    try:
        with st.spinner("Rewriting resume with Groq…"):
            existing = generate_edited_resume(st.session_state.analysis_id)
        st.toast("Resume rewrite saved", icon=":material/check_circle:")
        st.success(
            "Edited resume stored in Supabase. Review the text and download below.",
            icon=":material/check_circle:",
            title="Rewrite ready",
        )
    except Exception as exc:
        st.error(str(exc), icon=":material/error:")
        st.stop()

if not existing:
    st.info(
        "Click **Generate AI rewrite** to create an edited version for this analysis.",
        icon=":material/info:",
    )
    st.stop()

edited_text = existing["edited_text"]
suggestions = existing.get("section_suggestions") or {}

preview, tips = st.columns([1.4, 1], gap="large")
with preview:
    with st.container(border=True):
        st.subheader("Edited resume", icon=":material/article:")
        st.text_area(
            "Rewritten text",
            value=edited_text,
            height=480,
            label_visibility="collapsed",
        )
with tips:
    with st.container(border=True):
        st.subheader("Section suggestions", icon=":material/lightbulb:")
        for section in ("summary", "skills", "experience"):
            with st.expander(section.title(), expanded=section == "summary", icon=":material/notes:"):
                items = suggestions.get(section) or []
                if isinstance(items, list) and items:
                    for item in items:
                        st.markdown(f"- {item}")
                elif items:
                    st.write(items)
                else:
                    st.caption("No suggestions for this section.")

pdf_bytes, docx_bytes = build_exports(edited_text)
d1, d2 = st.columns(2, gap="medium")
with d1:
    st.download_button(
        "Download PDF",
        data=pdf_bytes,
        file_name="edited_resume.pdf",
        mime="application/pdf",
        icon=":material/picture_as_pdf:",
        width="stretch",
    )
with d2:
    st.download_button(
        "Download DOCX",
        data=docx_bytes,
        file_name="edited_resume.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        icon=":material/description:",
        width="stretch",
    )
