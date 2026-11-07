"""Upload resume and job description, then run analysis."""

from __future__ import annotations

import streamlit as st

from src.db import repositories as repo
from src.parsers.jd_parser import extract_jd_from_url, extract_text_from_upload
from src.parsers.resume_parser import extract_resume_text
from src.services.analysis import run_analysis
from src.ui.session import ensure_session_defaults, page_header, require_config

ensure_session_defaults()
require_config()
page_header(
    "Upload",
    "Add a resume and job description, then run the full analysis pipeline.",
    icon=":material/upload_file:",
)

left, right = st.columns(2, gap="large")

with left:
    with st.container(border=True):
        st.subheader("Resume", icon=":material/description:")
        st.caption("PDF or DOCX preferred for clean text extraction.")
        resume_file = st.file_uploader(
            "Resume file",
            type=["pdf", "docx"],
            key="resume_uploader",
            label_visibility="collapsed",
        )

with right:
    with st.container(border=True):
        st.subheader("Job description", icon=":material/work:")
        jd_mode = st.segmented_control(
            "JD source",
            options=["Upload file", "Job URL", "Paste text"],
            default="Paste text",
            required=True,
            key="jd_mode",
        )
        jd_file = None
        jd_url = ""
        jd_paste = ""
        if jd_mode == "Upload file":
            jd_file = st.file_uploader(
                "JD file",
                type=["pdf", "docx", "txt"],
                key="jd_uploader",
                label_visibility="collapsed",
            )
        elif jd_mode == "Job URL":
            jd_url = st.text_input(
                "Job posting URL",
                placeholder="https://...",
                help="Many boards block scraping. If it fails, paste the text instead.",
            )
        else:
            jd_paste = st.text_area(
                "Paste job description",
                height=220,
                placeholder="Paste the full job posting here…",
                label_visibility="collapsed",
            )

st.space("small")
run = st.button(
    "Save & run analysis",
    type="primary",
    icon=":material/play_arrow:",
    width="stretch",
)

if run:
    try:
        if resume_file is None:
            st.error("Please upload a resume.", icon=":material/upload_file:")
            st.stop()

        resume_bytes = resume_file.getvalue()
        resume_text = extract_resume_text(resume_file.name, resume_bytes)
        resume_row = repo.create_resume(resume_file.name, resume_text, resume_bytes)
        st.session_state.resume_id = resume_row["id"]
        st.session_state.resume_filename = resume_file.name

        if jd_mode == "Upload file":
            if jd_file is None:
                st.error("Please upload a job description file.", icon=":material/attach_file:")
                st.stop()
            jd_bytes = jd_file.getvalue()
            jd_text = extract_text_from_upload(jd_file.name, jd_bytes)
            jd_row = repo.create_job_description(
                source_type="upload",
                raw_text=jd_text,
                filename=jd_file.name,
                file_bytes=jd_bytes,
            )
            st.session_state.jd_label = jd_file.name
        elif jd_mode == "Job URL":
            if not jd_url.strip():
                st.error("Enter a job URL.", icon=":material/link_off:")
                st.stop()
            with st.spinner("Fetching job posting…"):
                jd_text = extract_jd_from_url(jd_url.strip())
            jd_row = repo.create_job_description(
                source_type="url",
                raw_text=jd_text,
                source_url=jd_url.strip(),
            )
            st.session_state.jd_label = jd_url.strip()
        else:
            if not jd_paste.strip():
                st.error("Paste a job description.", icon=":material/content_paste_off:")
                st.stop()
            jd_row = repo.create_job_description(
                source_type="paste",
                raw_text=jd_paste.strip(),
            )
            st.session_state.jd_label = "pasted JD"

        st.session_state.jd_id = jd_row["id"]

        with st.spinner(
            "Embedding documents, running vector search, then analyzing with Groq…"
        ):
            analysis = run_analysis(resume_row["id"], jd_row["id"])
        st.session_state.analysis_id = analysis["id"]
        st.success(
            f"Match score **{analysis.get('match_score')}**. Open Analyze for the full breakdown.",
            icon=":material/check_circle:",
            title="Analysis complete",
        )
        st.balloons()
        if st.button("View analysis", type="primary", icon=":material/analytics:"):
            st.switch_page("app_pages/analyze.py")
    except Exception as exc:
        st.error(str(exc), icon=":material/error:")

if st.session_state.analysis_id:
    st.caption(
        f"Latest session · resume `{st.session_state.resume_id}` · "
        f"JD `{st.session_state.jd_id}` · analysis `{st.session_state.analysis_id}`"
    )
