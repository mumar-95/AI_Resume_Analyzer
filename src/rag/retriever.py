"""Index documents and retrieve similar chunks from Supabase."""

from __future__ import annotations

from typing import Any

from src.db.repositories import delete_chunks_for_owner, insert_chunks, match_chunks
from src.rag.chunking import chunk_text
from src.rag.embeddings import embed_query, embed_texts


def index_document(owner_type: str, owner_id: str, text: str) -> int:
    chunks = chunk_text(text)
    if not chunks:
        return 0
    embeddings = embed_texts(chunks)
    delete_chunks_for_owner(owner_type, owner_id)
    rows = [
        {
            "owner_type": owner_type,
            "owner_id": owner_id,
            "chunk_index": idx,
            "content": chunk,
            "embedding": embedding,
        }
        for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings))
    ]
    insert_chunks(rows)
    return len(rows)


def retrieve_chunks(
    query: str,
    *,
    owner_type: str | None = None,
    owner_id: str | None = None,
    match_count: int = 8,
) -> list[dict[str, Any]]:
    embedding = embed_query(query)
    return match_chunks(
        embedding,
        match_count=match_count,
        owner_type=owner_type,
        owner_id=owner_id,
    )
