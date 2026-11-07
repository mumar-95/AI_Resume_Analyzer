"""Groq chat helpers with JSON extraction."""

from __future__ import annotations

import json
import re
from typing import Any

from groq import Groq

from src.config import get_settings


def get_groq_client() -> Groq:
    settings = get_settings()
    return Groq(api_key=settings.groq_api_key)


def chat_text(
    system_prompt: str,
    user_prompt: str,
    *,
    temperature: float = 0.3,
) -> str:
    settings = get_settings()
    client = get_groq_client()
    completion = client.chat.completions.create(
        model=settings.groq_model,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return (completion.choices[0].message.content or "").strip()


def _extract_json_block(text: str) -> Any:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        return json.loads(fence.group(1).strip())

    start_obj = text.find("{")
    start_arr = text.find("[")
    if start_obj == -1 and start_arr == -1:
        raise ValueError("Model response did not contain JSON.")

    if start_obj != -1 and (start_arr == -1 or start_obj < start_arr):
        end = text.rfind("}")
        snippet = text[start_obj : end + 1]
    else:
        end = text.rfind("]")
        snippet = text[start_arr : end + 1]
    return json.loads(snippet)


def chat_json(
    system_prompt: str,
    user_prompt: str,
    *,
    temperature: float = 0.2,
) -> Any:
    raw = chat_text(
        system_prompt + "\n\nReturn ONLY valid JSON. No markdown, no commentary.",
        user_prompt,
        temperature=temperature,
    )
    return _extract_json_block(raw)
