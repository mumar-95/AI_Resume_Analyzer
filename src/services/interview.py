"""Generate typed interview questions."""

from __future__ import annotations

from typing import Any

from src.db import repositories as repo
from src.llm.groq_client import chat_json
from src.rag.retriever import retrieve_chunks

INTERVIEW_SYSTEM = """You are an experienced technical interviewer.
Generate interview questions tailored to the candidate resume and job description.
Return JSON:
{
  "questions": [
    {
      "question_type": "technical" | "behavioral" | "role_specific",
      "question": "...",
      "hint": "short coaching hint"
    }
  ]
}
"""


def generate_interview_questions(
    analysis_id: str,
    *,
    count_per_type: int = 5,
) -> list[dict[str, Any]]:
    analysis = repo.get_analysis(analysis_id)
    if not analysis:
        raise ValueError("Analysis not found.")

    resume = repo.get_resume(analysis["resume_id"])
    jd = repo.get_job_description(analysis["jd_id"])
    if not resume or not jd:
        raise ValueError("Linked resume or JD missing.")

    jd_chunks = retrieve_chunks(
        "role responsibilities technologies soft skills",
        owner_type="jd",
        owner_id=analysis["jd_id"],
        match_count=5,
    )
    context = "\n".join(c.get("content", "") for c in jd_chunks)

    user_prompt = f"""Generate exactly {count_per_type} questions for EACH type:
technical, behavioral, role_specific.

RESUME:
{resume['raw_text'][:9000]}

JOB DESCRIPTION:
{jd['raw_text'][:9000]}

JD CONTEXT:
{context}

MISSING SKILLS:
{analysis.get('missing_skills')}
"""

    parsed = chat_json(INTERVIEW_SYSTEM, user_prompt, temperature=0.4)
    if isinstance(parsed, dict):
        items = parsed.get("questions") or []
    elif isinstance(parsed, list):
        items = parsed
    else:
        raise ValueError("Unexpected interview response shape.")

    cleaned: list[dict[str, Any]] = []
    allowed = {"technical", "behavioral", "role_specific"}
    for item in items:
        if not isinstance(item, dict):
            continue
        qtype = str(item.get("question_type", "")).strip().lower()
        question = str(item.get("question", "")).strip()
        if qtype not in allowed or not question:
            continue
        cleaned.append(
            {
                "question_type": qtype,
                "question": question,
                "hint": (str(item.get("hint") or "").strip() or None),
            }
        )

    if not cleaned:
        raise ValueError("No interview questions were generated.")

    return repo.create_interview_questions(analysis_id, cleaned)
