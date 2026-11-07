"""Resume vs JD analysis with local embeddings + vector search grounding."""

from __future__ import annotations

from typing import Any

from src.db import repositories as repo
from src.llm.groq_client import chat_json
from src.rag.retriever import index_document, retrieve_chunks

ANALYSIS_SYSTEM = """You are an expert ATS resume analyst and career coach.
Compare the resume to the job description carefully.
Do not invent skills the candidate does not demonstrate.
Return a JSON object with exactly these keys:
- match_score: number 0-100
- missing_skills: string array
- matched_keywords: string array
- ats_tips: string array
- strengths: string array
- weaknesses: string array
"""


def _format_chunks(chunks: list[dict[str, Any]]) -> str:
    if not chunks:
        return "(no retrieved chunks)"
    lines = []
    for i, chunk in enumerate(chunks, start=1):
        sim = chunk.get("similarity")
        prefix = f"[{i} similarity={sim:.3f}]" if isinstance(sim, (int, float)) else f"[{i}]"
        lines.append(f"{prefix} {chunk.get('content', '')}")
    return "\n\n".join(lines)


def run_analysis(resume_id: str, jd_id: str) -> dict[str, Any]:
    resume = repo.get_resume(resume_id)
    jd = repo.get_job_description(jd_id)
    if not resume or not jd:
        raise ValueError("Resume or job description not found.")

    index_document("resume", resume_id, resume["raw_text"])
    index_document("jd", jd_id, jd["raw_text"])

    query = "skills requirements responsibilities qualifications keywords experience"
    jd_chunks = retrieve_chunks(query, owner_type="jd", owner_id=jd_id, match_count=6)
    resume_chunks = retrieve_chunks(
        query, owner_type="resume", owner_id=resume_id, match_count=6
    )

    user_prompt = f"""RESUME TEXT:
{resume['raw_text'][:12000]}

JOB DESCRIPTION TEXT:
{jd['raw_text'][:12000]}

RETRIEVED JD CHUNKS:
{_format_chunks(jd_chunks)}

RETRIEVED RESUME CHUNKS:
{_format_chunks(resume_chunks)}

Produce the analysis JSON now."""

    parsed = chat_json(ANALYSIS_SYSTEM, user_prompt)
    if not isinstance(parsed, dict):
        raise ValueError("Unexpected analysis response shape.")

    normalized = {
        "match_score": float(parsed.get("match_score", 0)),
        "missing_skills": list(parsed.get("missing_skills") or []),
        "matched_keywords": list(parsed.get("matched_keywords") or []),
        "ats_tips": list(parsed.get("ats_tips") or []),
        "strengths": list(parsed.get("strengths") or []),
        "weaknesses": list(parsed.get("weaknesses") or []),
    }
    saved = repo.create_analysis(resume_id, jd_id, normalized)
    return saved
