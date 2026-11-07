"""Extract text from resume PDF and DOCX uploads."""

from __future__ import annotations

import io
import re
from pathlib import Path

from docx import Document
from pypdf import PdfReader


def _normalize_whitespace(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_text_from_pdf(data: bytes) -> str:
    reader = PdfReader(io.BytesIO(data))
    parts: list[str] = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        if page_text.strip():
            parts.append(page_text)
    return _normalize_whitespace("\n".join(parts))


def extract_text_from_docx(data: bytes) -> str:
    document = Document(io.BytesIO(data))
    parts = [p.text for p in document.paragraphs if p.text and p.text.strip()]
    for table in document.tables:
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if cells:
                parts.append(" | ".join(cells))
    return _normalize_whitespace("\n".join(parts))


def extract_resume_text(filename: str, data: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        text = extract_text_from_pdf(data)
    elif suffix in {".docx", ".doc"}:
        if suffix == ".doc":
            raise ValueError("Legacy .doc is not supported. Please upload PDF or DOCX.")
        text = extract_text_from_docx(data)
    else:
        raise ValueError("Unsupported resume type. Upload a PDF or DOCX file.")

    if not text:
        raise ValueError("Could not extract text from the resume. Try another file.")
    return text
