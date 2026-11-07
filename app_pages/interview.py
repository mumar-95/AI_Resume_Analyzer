"""Generate and browse interview questions by type."""

from __future__ import annotations

import streamlit as st

from src.db import repositories as repo
from src.services.interview import generate_interview_questions
from src.ui.session import ensure_session_defaults, page_header, require_config

ensure_session_defaults()
require_config()
page_header(
    "Interview prep",
    "Technical, behavioral, and role-specific questions grounded in your analysis.",
    icon=":material/forum:",
)

if not st.session_state.analysis_id:
    st.warning(
        "Run an analysis first so questions can target the same role and gaps.",
        icon=":material/warning:",
        title="Analysis required",
    )
    if st.button("Go to upload", type="primary", icon=":material/upload_file:"):
        st.switch_page("app_pages/upload.py")
    st.stop()

controls = st.container(horizontal=True, gap="medium", vertical_alignment="bottom")
with controls:
    count = st.slider("Questions per type", min_value=3, max_value=10, value=5)
    generate = st.button(
        "Generate questions",
        type="primary",
        icon=":material/quiz:",
    )

if generate:
    try:
        with st.spinner("Generating questions with Groq…"):
            generate_interview_questions(
                st.session_state.analysis_id,
                count_per_type=count,
            )
        st.toast("Questions saved", icon=":material/check_circle:")
        st.success(
            "A fresh set was stored in Supabase. Browse by type below.",
            icon=":material/check_circle:",
            title="Questions ready",
        )
    except Exception as exc:
        st.error(str(exc), icon=":material/error:")

questions = repo.list_interview_questions(st.session_state.analysis_id)
if not questions:
    st.info(
        "No questions yet. Choose how many per type, then generate a set.",
        icon=":material/info:",
    )
    st.stop()

grouped = {"technical": [], "behavioral": [], "role_specific": []}
for q in questions:
    grouped.setdefault(q["question_type"], []).append(q)

tabs = st.tabs(
    [
        ":material/terminal: Technical",
        ":material/psychology: Behavioral",
        ":material/work: Role-specific",
    ]
)
mapping = [
    ("technical", tabs[0]),
    ("behavioral", tabs[1]),
    ("role_specific", tabs[2]),
]

for key, tab in mapping:
    with tab:
        items = grouped.get(key) or []
        if not items:
            st.caption("No questions for this type yet.")
            continue
        st.caption(f"{len(items)} questions")
        for i, item in enumerate(items, start=1):
            with st.container(border=True):
                st.markdown(f"**{i}. {item['question']}**")
                if item.get("hint"):
                    st.caption(f"Hint · {item['hint']}")
