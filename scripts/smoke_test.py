"""Local smoke test that does not require API keys."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.config import EMBEDDING_DIMS
from src.llm.groq_client import _extract_json_block
from src.rag.chunking import chunk_text
from src.rag.embeddings import embed_query, embed_texts
from src.services.exporters import export_docx_bytes, export_pdf_bytes

chunks = chunk_text("hello world " * 200)
assert chunks, "chunking failed"

pdf = export_pdf_bytes("Test resume\n\nSkills: Python")
docx = export_docx_bytes("Test resume")
assert pdf.startswith(b"%PDF")
assert len(docx) > 100

assert _extract_json_block('{"a": 1}')["a"] == 1
assert _extract_json_block('```json\n{"b": 2}\n```')["b"] == 2

query_vec = embed_query("python developer with fastapi experience")
batch = embed_texts(["alpha", "beta"])
assert len(query_vec) == EMBEDDING_DIMS
assert len(batch) == 2 and len(batch[0]) == EMBEDDING_DIMS

print("smoke_test ok")
