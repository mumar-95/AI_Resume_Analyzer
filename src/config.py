"""Load environment settings for the AI Resume Analyzer."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMS = 384


@dataclass(frozen=True)
class Settings:
    groq_api_key: str
    groq_model: str
    embedding_model: str
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str
    supabase_storage_bucket: str

    @property
    def supabase_key(self) -> str:
        """Prefer service role for local single-user demo."""
        return self.supabase_service_role_key or self.supabase_anon_key

    def missing_keys(self) -> list[str]:
        required = {
            "GROQ_API_KEY": self.groq_api_key,
            "SUPABASE_URL": self.supabase_url,
            "SUPABASE_KEY": self.supabase_key,
        }
        return [name for name, value in required.items() if not value]


def _first_env(*names: str) -> str:
    for name in names:
        value = os.getenv(name, "").strip()
        if value:
            return value
    return ""


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        groq_api_key=_first_env("GROQ_API_KEY"),
        groq_model=_first_env("GROQ_MODEL") or "llama-3.3-70b-versatile",
        embedding_model=_first_env("EMBEDDING_MODEL") or DEFAULT_EMBEDDING_MODEL,
        supabase_url=_first_env("SUPABASE_URL"),
        # Support both classic and newer Supabase dashboard env names.
        supabase_anon_key=_first_env(
            "SUPABASE_ANON_KEY",
            "SUPABASE_PUBLISHABLE_KEY",
        ),
        supabase_service_role_key=_first_env(
            "SUPABASE_SERVICE_ROLE_KEY",
            "SUPABASE_SECRET_KEY",
        ),
        supabase_storage_bucket=_first_env("SUPABASE_STORAGE_BUCKET") or "resumes",
    )
