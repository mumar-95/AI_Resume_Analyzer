"""Show analysis results and history."""

from __future__ import annotations

import streamlit as st

from src.db import repositories as repo
from src.ui.session import (
    ensure_session_defaults,
    page_header,
    render_bullet_list,
    render_keyword_badges,
    require_config,
    score_label,
)

ensure_session_defaults()
require_config()
page_header(
    "Analyze",
    "Match score, skill gaps, keywords, ATS tips, and strengths vs weaknesses.",
    icon=":material/analytics:",
)

recent = repo.list_recent_analyses(limit=15)
if not recent:
    st.info(
        "No analyses yet. Upload a resume and JD to create your first report.",
        icon=":material/info:",
        title="Nothing to show",
    )
    if st.button("Go to upload", type="primary", icon=":material/upload_file:"):
        st.switch_page("app_pages/upload.py")
    st.stop()

labels = {
    row["id"]: f"{row['created_at'][:19]} · score {row.get('match_score')}"
    for row in recent
}
options = list(labels.keys())
default_idx = 0
if st.session_state.analysis_id in labels:
    default_idx = options.index(st.session_state.analysis_id)

selected = st.selectbox(
    "Load analysis",
    options=options,
    index=default_idx,
    format_func=lambda x: labels[x],
    help="Pick a previous run or keep the latest from this session.",
)
st.session_state.analysis_id = selected

analysis = repo.get_analysis(st.session_state.analysis_id)
if not analysis:
    st.error("Could not load analysis.", icon=":material/error:")
    st.stop()

st.session_state.resume_id = analysis["resume_id"]
st.session_state.jd_id = analysis["jd_id"]

score = analysis.get("match_score") or 0
label, color = score_label(score)
missing_n = len(analysis.get("missing_skills") or [])
matched_n = len(analysis.get("matched_keywords") or [])

m1, m2, m3 = st.columns(3, gap="medium")
m1.metric(
    "Match score",
    f"{score}",
    delta=label,
    delta_color="off",
    border=True,
    icon=":material/speed:",
)
m2.metric(
    "Missing skills",
    missing_n,
    border=True,
    icon=":material/playlist_remove:",
)
m3.metric(
    "Matched keywords",
    matched_n,
    border=True,
    icon=":material/sell:",
)

st.progress(min(max(float(score) / 100.0, 0.0), 1.0), text=f"{label} · {score}/100")
st.badge(label, color=color, icon=":material/insights:")

col_a, col_b = st.columns(2, gap="large")
with col_a:
    with st.container(border=True):
        st.subheader("Missing skills", icon=":material/playlist_remove:")
        render_bullet_list(analysis.get("missing_skills"), empty="No major gaps flagged.")
    st.space("small")
    with st.container(border=True):
        st.subheader("Strengths", icon=":material/thumb_up:")
        render_bullet_list(analysis.get("strengths"), empty="No strengths listed.")
with col_b:
    with st.container(border=True):
        st.subheader("Matched keywords", icon=":material/sell:")
        render_keyword_badges(analysis.get("matched_keywords"))
    st.space("small")
    with st.container(border=True):
        st.subheader("Weaknesses", icon=":material/thumb_down:")
        render_bullet_list(analysis.get("weaknesses"), empty="No weaknesses listed.")

with st.container(border=True):
    st.subheader("ATS tips", icon=":material/fact_check:")
    render_bullet_list(analysis.get("ats_tips"), empty="No ATS tips returned.")

actions = st.container(horizontal=True, gap="small")
with actions:
    if st.button("Rewrite resume", type="primary", icon=":material/edit_note:"):
        st.switch_page("app_pages/edit_resume.py")
    if st.button("Interview prep", icon=":material/forum:"):
        st.switch_page("app_pages/interview.py")

with st.expander("Raw analysis JSON", icon=":material/data_object:"):
    st.json(analysis.get("raw_response") or analysis)
