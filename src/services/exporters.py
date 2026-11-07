"""Export edited resume text to PDF and DOCX bytes."""

from __future__ import annotations

import io
import re

from docx import Document
from docx.shared import Pt
from fpdf import FPDF


def _paragraphs(text: str) -> list[str]:
    parts = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if parts:
        return parts
    return [line.strip() for line in text.splitlines() if line.strip()] or [text]


def export_docx_bytes(text: str) -> bytes:
    document = Document()
    style = document.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)

    for block in _paragraphs(text):
        for line in block.splitlines():
            document.add_paragraph(line)
        document.add_paragraph("")

    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


class _ResumePDF(FPDF):
    def footer(self) -> None:
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")


def export_pdf_bytes(text: str) -> bytes:
    pdf = _ResumePDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)

    # fpdf2 needs latin-1 compatible or use unicode fonts; sanitize smartly
    safe = (
        text.replace("•", "-")
        .replace("–", "-")
        .replace("—", "-")
        .replace("’", "'")
        .replace("“", '"')
        .replace("”", '"')
    )
    try:
        safe.encode("latin-1")
    except UnicodeEncodeError:
        safe = safe.encode("latin-1", errors="replace").decode("latin-1")

    for block in _paragraphs(safe):
        pdf.multi_cell(0, 6, block)
        pdf.ln(3)

    out = pdf.output()
    if isinstance(out, (bytes, bytearray)):
        return bytes(out)
    return out.encode("latin-1")
