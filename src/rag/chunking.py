"""Simple character-based chunking approximating token windows."""

from __future__ import annotations


def chunk_text(
    text: str,
    chunk_size: int = 1800,
    overlap: int = 250,
) -> list[str]:
    """Split text into overlapping chunks (~500–800 tokens at ~3–4 chars/token)."""
    cleaned = " ".join(text.split())
    if not cleaned:
        return []
    if len(cleaned) <= chunk_size:
        return [cleaned]

    chunks: list[str] = []
    start = 0
    length = len(cleaned)
    while start < length:
        end = min(start + chunk_size, length)
        if end < length:
            # Prefer breaking on sentence/space boundaries
            window = cleaned[start:end]
            split_at = max(window.rfind(". "), window.rfind(" "))
            if split_at > chunk_size // 3:
                end = start + split_at + 1
        chunk = cleaned[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= length:
            break
        start = max(end - overlap, start + 1)
    return chunks
