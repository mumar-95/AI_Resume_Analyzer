"""AI resume rewriting and export helpers."""

from __future__ import annotations

from typing import Any

from src.db import repositories as repo
from src.llm.groq_client import chat_json
from src.rag.retriever import retrieve_chunks
from src.services.exporters import export_docx_bytes, export_pdf_bytes

EDIT_SYSTEM = """You are an expert resume writer and ATS specialist.
Rewrite the resume to better match the job description.
CRITICAL RULES:
- Never invent employers, degrees, dates, or achievements.
- You may rephrase existing content and reorder/emphasize relevant skills.
- Keep factual content grounded in the original resume.
Return JSON with:
{
  "edited_text": "full rewritten resume as plain text",
  "section_suggestions": {
    "summary": ["..."],
    "skills": ["..."],
    "experience": ["..."]
  }
}
"""


def generate_edited_resume(analysis_id: str) -> dict[str, Any]:
    analysis = repo.get_analysis(analysis_id)
    if not analysis:
        raise ValueError("Analysis not found.")

    resume = repo.get_resume(analysis["resume_id"])
    jd = repo.get_job_description(analysis["jd_id"])
    if not resume or not jd:
        raise ValueError("Linked resume or JD missing.")

    jd_chunks = retrieve_chunks(
        "key requirements skills tools responsibilities",
        owner_type="jd",
        owner_id=analysis["jd_id"],
        match_count=5,
    )
    chunk_text = "\n".join(c.get("content", "") for c in jd_chunks)

    user_prompt = f"""ORIGINAL RESUME:
{resume['raw_text'][:12000]}

JOB DESCRIPTION:
{jd['raw_text'][:10000]}

MISSING SKILLS FROM ANALYSIS:
{analysis.get('missing_skills')}

MATCHED KEYWORDS:
{analysis.get('matched_keywords')}

JD RAG CONTEXT:
{chunk_text}

Rewrite the resume now as JSON."""

    parsed = chat_json(EDIT_SYSTEM, user_prompt, temperature=0.35)
    if not isinstance(parsed, dict):
        raise ValueError("Unexpected edit response shape.")

    edited_text = str(parsed.get("edited_text") or "").strip()
    suggestions = parsed.get("section_suggestions") or {}
    if not edited_text:
        raise ValueError("Model returned an empty edited resume.")

    saved = repo.create_resume_edit(analysis_id, edited_text, suggestions)
    return saved


def build_exports(edited_text: str) -> tuple[bytes, bytes]:
    return export_pdf_bytes(edited_text), export_docx_bytes(edited_text)
