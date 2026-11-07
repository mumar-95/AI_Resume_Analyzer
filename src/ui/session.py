"""Session-state and shared UI helpers for Streamlit pages."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import get_settings  # noqa: E402


SESSION_KEYS = (
    "resume_id",
    "jd_id",
    "analysis_id",
    "resume_filename",
    "jd_label",
)

WORKFLOW_STEPS = (
    ("Upload", ":material/upload_file:"),
    ("Analyze", ":material/analytics:"),
    ("Edit", ":material/edit_note:"),
    ("Interview", ":material/forum:"),
)


def ensure_session_defaults() -> None:
    for key in SESSION_KEYS:
        if key not in st.session_state:
            st.session_state[key] = None


def require_config() -> bool:
    settings = get_settings()
    missing = settings.missing_keys()
    if missing:
        st.error(
            "Missing configuration: "
            + ", ".join(missing)
            + ". Copy `.env.example` to `.env` and fill in your keys.",
            icon=":material/key_off:",
        )
        st.stop()
        return False
    return True


def page_header(
    title: str,
    subtitle: str | None = None,
    *,
    icon: str | None = None,
) -> None:
    st.title(title, icon=icon)
    if subtitle:
        st.caption(subtitle)


def render_sidebar_status() -> None:
    """Compact session progress in the sidebar."""
    ensure_session_defaults()
    settings = get_settings()
    missing = settings.missing_keys()

    with st.sidebar:
        st.markdown("### Session")
        if missing:
            st.badge("Setup needed", icon=":material/warning:", color="orange")
        else:
            st.badge("Ready", icon=":material/check_circle:", color="green")

        resume_ok = bool(st.session_state.resume_id)
        jd_ok = bool(st.session_state.jd_id)
        analysis_ok = bool(st.session_state.analysis_id)

        st.caption("Resume")
        if resume_ok:
            st.badge(
                st.session_state.resume_filename or "Uploaded",
                icon=":material/description:",
                color="green",
            )
        else:
            st.badge("Not uploaded", icon=":material/pending:", color="gray")

        st.caption("Job description")
        if jd_ok:
            label = st.session_state.jd_label or "Loaded"
            short = label if len(str(label)) < 28 else f"{str(label)[:25]}..."
            st.badge(short, icon=":material/work:", color="green")
        else:
            st.badge("Not provided", icon=":material/pending:", color="gray")

        st.caption("Analysis")
        if analysis_ok:
            st.badge("Complete", icon=":material/analytics:", color="primary")
        else:
            st.badge("Pending", icon=":material/pending:", color="gray")

        done = sum([resume_ok, jd_ok, analysis_ok])
        st.progress(done / 3.0, text=f"{done}/3 inputs ready")


def score_label(score: float | int | None) -> tuple[str, str]:
    value = float(score or 0)
    if value >= 80:
        return "Strong match", "green"
    if value >= 60:
        return "Solid match", "blue"
    if value >= 40:
        return "Needs work", "orange"
    return "Weak match", "red"


def render_bullet_list(items: list | None, empty: str = "None listed") -> None:
    items = items or []
    if not items:
        st.caption(empty)
        return
    for item in items:
        st.markdown(f"- {item}")


def render_keyword_badges(items: list | None) -> None:
    items = items or []
    if not items:
        st.caption("No keywords matched yet.")
        return
    chips = " ".join(f":green-badge[{item}]" for item in items[:40])
    st.markdown(chips)


def workflow_step_index() -> int:
    if st.session_state.get("analysis_id"):
        return 2
    if st.session_state.get("resume_id") and st.session_state.get("jd_id"):
        return 1
    return 0
