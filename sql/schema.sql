-- AI Resume Analyzer — Supabase schema (demo)
-- Run this in the Supabase SQL Editor after creating your project.
-- Then create a Storage bucket named "resumes" (Dashboard → Storage).

create extension if not exists vector with schema extensions;
create extension if not exists "uuid-ossp" with schema extensions;

-- ---------------------------------------------------------------------------
-- Tables
-- ---------------------------------------------------------------------------

create table if not exists public.resumes (
  id uuid primary key default gen_random_uuid(),
  filename text not null,
  file_path text,
  raw_text text not null,
  created_at timestamptz not null default now()
);

create table if not exists public.job_descriptions (
  id uuid primary key default gen_random_uuid(),
  source_type text not null check (source_type in ('upload', 'url', 'paste')),
  source_url text,
  filename text,
  raw_text text not null,
  created_at timestamptz not null default now()
);

create table if not exists public.analyses (
  id uuid primary key default gen_random_uuid(),
  resume_id uuid not null references public.resumes (id) on delete cascade,
  jd_id uuid not null references public.job_descriptions (id) on delete cascade,
  match_score numeric(5, 2),
  missing_skills jsonb not null default '[]'::jsonb,
  matched_keywords jsonb not null default '[]'::jsonb,
  ats_tips jsonb not null default '[]'::jsonb,
  strengths jsonb not null default '[]'::jsonb,
  weaknesses jsonb not null default '[]'::jsonb,
  raw_response jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.resume_edits (
  id uuid primary key default gen_random_uuid(),
  analysis_id uuid not null references public.analyses (id) on delete cascade,
  edited_text text not null,
  section_suggestions jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.interview_questions (
  id uuid primary key default gen_random_uuid(),
  analysis_id uuid not null references public.analyses (id) on delete cascade,
  question_type text not null check (
    question_type in ('technical', 'behavioral', 'role_specific')
  ),
  question text not null,
  hint text,
  created_at timestamptz not null default now()
);

-- Local fastembed MiniLM => 384 dimensions (no OpenAI)
create table if not exists public.document_chunks (
  id uuid primary key default gen_random_uuid(),
  owner_type text not null check (owner_type in ('resume', 'jd')),
  owner_id uuid not null,
  chunk_index integer not null,
  content text not null,
  embedding extensions.vector(384),
  created_at timestamptz not null default now()
);

create index if not exists document_chunks_owner_idx
  on public.document_chunks (owner_type, owner_id);

create index if not exists analyses_created_at_idx
  on public.analyses (created_at desc);

-- Optional after you have data (HNSW):
-- create index document_chunks_embedding_idx
--   on public.document_chunks
--   using hnsw (embedding extensions.vector_cosine_ops);

-- ---------------------------------------------------------------------------
-- Vector similarity RPC
-- ---------------------------------------------------------------------------

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

-- If you previously created the 1536-dim OpenAI schema, run sql/migrate_embeddings_384.sql.

-- ---------------------------------------------------------------------------
-- Demo RLS: open policies for local portfolio demo only.
-- ---------------------------------------------------------------------------

alter table public.resumes enable row level security;
alter table public.job_descriptions enable row level security;
alter table public.analyses enable row level security;
alter table public.resume_edits enable row level security;
alter table public.interview_questions enable row level security;
alter table public.document_chunks enable row level security;

drop policy if exists "demo_all_resumes" on public.resumes;
create policy "demo_all_resumes" on public.resumes for all using (true) with check (true);

drop policy if exists "demo_all_job_descriptions" on public.job_descriptions;
create policy "demo_all_job_descriptions" on public.job_descriptions for all using (true) with check (true);

drop policy if exists "demo_all_analyses" on public.analyses;
create policy "demo_all_analyses" on public.analyses for all using (true) with check (true);

drop policy if exists "demo_all_resume_edits" on public.resume_edits;
create policy "demo_all_resume_edits" on public.resume_edits for all using (true) with check (true);

drop policy if exists "demo_all_interview_questions" on public.interview_questions;
create policy "demo_all_interview_questions" on public.interview_questions for all using (true) with check (true);

drop policy if exists "demo_all_document_chunks" on public.document_chunks;
create policy "demo_all_document_chunks" on public.document_chunks for all using (true) with check (true);

-- Storage (Dashboard → Storage):
-- 1. Create private bucket "resumes".
-- 2. Optional: create bucket "job_descriptions".
