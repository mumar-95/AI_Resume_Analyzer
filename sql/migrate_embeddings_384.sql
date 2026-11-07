-- Migrate document_chunks from OpenAI 1536-dim embeddings to local MiniLM 384-dim.
-- Run in Supabase SQL Editor if you already applied the old schema.

drop function if exists public.match_document_chunks(
  extensions.vector(1536), integer, text, uuid
);

truncate table public.document_chunks;

alter table public.document_chunks
  alter column embedding type extensions.vector(384)
  using null;

create or replace function public.match_document_chunks(
  query_embedding extensions.vector(384),
  match_count integer default 8,
  filter_owner_type text default null,
  filter_owner_id uuid default null
)
returns table (
  id uuid,
  content text,
  owner_type text,
  owner_id uuid,
  chunk_index integer,
  similarity float
)
language sql
stable
as $$
  select
    dc.id,
    dc.content,
    dc.owner_type,
    dc.owner_id,
    dc.chunk_index,
    1 - (dc.embedding <=> query_embedding) as similarity
  from public.document_chunks dc
  where
    dc.embedding is not null
    and (filter_owner_type is null or dc.owner_type = filter_owner_type)
    and (filter_owner_id is null or dc.owner_id = filter_owner_id)
  order by dc.embedding <=> query_embedding
  limit greatest(match_count, 1);
$$;

grant execute on function public.match_document_chunks(
  extensions.vector(384), integer, text, uuid
) to anon, authenticated, service_role;
