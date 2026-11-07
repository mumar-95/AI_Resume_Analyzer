"""Home overview and workflow guide."""

from __future__ import annotations

import streamlit as st

from src.config import get_settings
from src.ui.session import ensure_session_defaults, page_header, workflow_step_index

ensure_session_defaults()
page_header(
    "AI Resume Analyzer",
    "Compare your resume to a role, close skill gaps, rewrite with AI, and rehearse interviews.",
    icon=":material/description:",
)

settings = get_settings()
missing = settings.missing_keys()
step = workflow_step_index()

status = st.container(horizontal=True, gap="small")
with status:
    if missing:
        st.badge("Setup incomplete", icon=":material/warning:", color="orange")
    else:
        st.badge("Configured", icon=":material/verified:", color="green")
    st.badge("Local embeddings", icon=":material/psychology:", color="blue")
    st.badge("Groq reasoning", icon=":material/bolt:", color="primary")

st.space("small")

if missing:
    st.warning(
        "Copy `.env.example` → `.env`, add your API keys, run `sql/schema.sql` "
        "(or `sql/migrate_embeddings_384.sql` if you still have 1536-dim vectors), "
        "and create a `resumes` storage bucket.",
        icon=":material/settings:",
        title="Finish setup before analyzing",
    )
else:
    st.success(
        "Keys look good. Start on Upload, then move through Analyze → Edit → Interview.",
        icon=":material/rocket_launch:",
        title="You're ready",
    )

st.subheader("Workflow", icon=":material/route:")

cards = st.container(horizontal=True, gap="medium")
steps = [
    (
        "1. Upload",
        ":material/upload_file:",
        "Add a PDF/DOCX resume and a JD via file, URL, or paste.",
        step >= 0,
    ),
    (
        "2. Analyze",
        ":material/analytics:",
        "See match score, missing skills, keywords, and ATS tips.",
        step >= 1,
    ),
    (
        "3. Edit",
        ":material/edit_note:",
        "Rewrite for the target role without inventing experience.",
        step >= 2,
    ),
    (
        "4. Interview",
        ":material/forum:",
        "Practice technical, behavioral, and role-specific questions.",
        step >= 2,
    ),
]

with cards:
    for title, icon, blurb, active in steps:
        with st.container(border=True, height="stretch"):
            st.markdown(f"**{icon} {title}**")
            st.caption(blurb)
            if active and title.startswith(("2.", "3.", "4.")) and st.session_state.analysis_id:
                st.badge("Unlocked", color="green", icon=":material/lock_open:")
            elif title.startswith("1."):
                st.badge("Start here", color="primary", icon=":material/flag:")
            else:
                st.badge("Locked", color="gray", icon=":material/lock:")

st.space("medium")

cta = st.container(horizontal=True, gap="small", vertical_alignment="center")
with cta:
    if st.button("Go to upload", type="primary", icon=":material/upload_file:"):
        st.switch_page("app_pages/upload.py")
    if st.session_state.analysis_id and st.button(
        "Open latest analysis",
        icon=":material/analytics:",
    ):
        st.switch_page("app_pages/analyze.py")

st.caption(
    f"Embedding model: `{settings.embedding_model}` · vector search in Supabase · no OpenAI embeddings"
)
