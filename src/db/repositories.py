"""CRUD helpers for Supabase tables and storage."""

from __future__ import annotations

import uuid
from typing import Any

from src.config import get_settings
from src.db.supabase_client import get_supabase


def upload_file(path: str, data: bytes, content_type: str) -> str:
    settings = get_settings()
    client = get_supabase()
    bucket = settings.supabase_storage_bucket
    client.storage.from_(bucket).upload(
        path,
        data,
        file_options={"content-type": content_type, "upsert": "true"},
    )
    return f"{bucket}/{path}"


def create_resume(filename: str, raw_text: str, file_bytes: bytes | None = None) -> dict[str, Any]:
    client = get_supabase()
    file_path = None
    if file_bytes is not None:
        object_name = f"resumes/{uuid.uuid4()}_{filename}"
        content_type = (
            "application/pdf"
            if filename.lower().endswith(".pdf")
            else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        try:
            file_path = upload_file(object_name, file_bytes, content_type)
        except Exception:
            # Storage may be unconfigured in early setup; still save text row.
            file_path = None

    payload = {"filename": filename, "file_path": file_path, "raw_text": raw_text}
    result = client.table("resumes").insert(payload).execute()
    return result.data[0]


def create_job_description(
    *,
    source_type: str,
    raw_text: str,
    source_url: str | None = None,
    filename: str | None = None,
    file_bytes: bytes | None = None,
) -> dict[str, Any]:
    client = get_supabase()
    if file_bytes is not None and filename:
        object_name = f"job_descriptions/{uuid.uuid4()}_{filename}"
        try:
            upload_file(object_name, file_bytes, "application/octet-stream")
        except Exception:
            pass

    payload = {
        "source_type": source_type,
        "source_url": source_url,
        "filename": filename,
        "raw_text": raw_text,
    }
    result = client.table("job_descriptions").insert(payload).execute()
    return result.data[0]


def create_analysis(
    resume_id: str,
    jd_id: str,
    analysis: dict[str, Any],
) -> dict[str, Any]:
    client = get_supabase()
    payload = {
        "resume_id": resume_id,
        "jd_id": jd_id,
        "match_score": analysis.get("match_score"),
        "missing_skills": analysis.get("missing_skills", []),
        "matched_keywords": analysis.get("matched_keywords", []),
        "ats_tips": analysis.get("ats_tips", []),
        "strengths": analysis.get("strengths", []),
        "weaknesses": analysis.get("weaknesses", []),
        "raw_response": analysis,
    }
    result = client.table("analyses").insert(payload).execute()
    return result.data[0]


def create_resume_edit(
    analysis_id: str,
    edited_text: str,
    section_suggestions: dict[str, Any],
) -> dict[str, Any]:
    client = get_supabase()
    payload = {
        "analysis_id": analysis_id,
        "edited_text": edited_text,
        "section_suggestions": section_suggestions,
    }
    result = client.table("resume_edits").insert(payload).execute()
    return result.data[0]


def create_interview_questions(
    analysis_id: str,
    questions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not questions:
        return []
    client = get_supabase()
    rows = [
        {
            "analysis_id": analysis_id,
            "question_type": q["question_type"],
            "question": q["question"],
            "hint": q.get("hint"),
        }
        for q in questions
    ]
    result = client.table("interview_questions").insert(rows).execute()
    return result.data or []


def get_resume(resume_id: str) -> dict[str, Any] | None:
    client = get_supabase()
    result = client.table("resumes").select("*").eq("id", resume_id).limit(1).execute()
    return result.data[0] if result.data else None


def get_job_description(jd_id: str) -> dict[str, Any] | None:
    client = get_supabase()
    result = (
        client.table("job_descriptions").select("*").eq("id", jd_id).limit(1).execute()
    )
    return result.data[0] if result.data else None


def get_analysis(analysis_id: str) -> dict[str, Any] | None:
    client = get_supabase()
    result = client.table("analyses").select("*").eq("id", analysis_id).limit(1).execute()
    return result.data[0] if result.data else None


def list_recent_analyses(limit: int = 10) -> list[dict[str, Any]]:
    client = get_supabase()
    result = (
        client.table("analyses")
        .select("id, resume_id, jd_id, match_score, created_at")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return result.data or []


def get_latest_resume_edit(analysis_id: str) -> dict[str, Any] | None:
    client = get_supabase()
    result = (
        client.table("resume_edits")
        .select("*")
        .eq("analysis_id", analysis_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def list_interview_questions(analysis_id: str) -> list[dict[str, Any]]:
    client = get_supabase()
    result = (
        client.table("interview_questions")
        .select("*")
        .eq("analysis_id", analysis_id)
        .order("created_at")
        .execute()
    )
    return result.data or []


def delete_chunks_for_owner(owner_type: str, owner_id: str) -> None:
    client = get_supabase()
    (
        client.table("document_chunks")
        .delete()
        .eq("owner_type", owner_type)
        .eq("owner_id", owner_id)
        .execute()
    )


def insert_chunks(rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    client = get_supabase()
    # Insert in batches to avoid payload limits
    batch_size = 50
    for i in range(0, len(rows), batch_size):
        client.table("document_chunks").insert(rows[i : i + batch_size]).execute()


def match_chunks(
    query_embedding: list[float],
    *,
    match_count: int = 8,
    owner_type: str | None = None,
    owner_id: str | None = None,
) -> list[dict[str, Any]]:
    client = get_supabase()
    params: dict[str, Any] = {
        "query_embedding": query_embedding,
        "match_count": match_count,
        "filter_owner_type": owner_type,
        "filter_owner_id": owner_id,
    }
    result = client.rpc("match_document_chunks", params).execute()
    return result.data or []
