"""AI Resume Analyzer — Streamlit entrypoint with modern navigation."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from src.ui.session import ensure_session_defaults, render_sidebar_status

st.set_page_config(
    page_title="AI Resume Analyzer",
    page_icon=":material/description:",
    layout="wide",
    initial_sidebar_state="expanded",
)

ensure_session_defaults()

pages = [
    st.Page(
        "app_pages/home.py",
        title="Home",
        icon=":material/home:",
        default=True,
    ),
    st.Page(
        "app_pages/upload.py",
        title="Upload",
        icon=":material/upload_file:",
    ),
    st.Page(
        "app_pages/analyze.py",
        title="Analyze",
        icon=":material/analytics:",
    ),
    st.Page(
        "app_pages/edit_resume.py",
        title="Edit resume",
        icon=":material/edit_note:",
    ),
    st.Page(
        "app_pages/interview.py",
        title="Interview",
        icon=":material/forum:",
    ),
]

page = st.navigation(pages, position="top")
render_sidebar_status()
page.run()
