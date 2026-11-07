# AI Resume Analyzer

Single-user Streamlit portfolio demo that compares a resume to a job description with **RAG** (local embeddings + Supabase pgvector), reasons with **Groq**, rewrites the resume, and generates typed interview questions. All artifacts are stored in **Supabase**.

## Features

- Upload resume (**PDF / DOCX**)
- Provide JD via **file upload**, **job URL scrape**, or **paste**
- Match score, missing skills, matched keywords, ATS tips, strengths & weaknesses
- AI-edited resume with section suggestions + **PDF / DOCX** download
- Interview questions by type: technical, behavioral, role-specific
- Persistence: resumes, JDs, analyses, edits, questions, and vector chunks in Supabase

## Architecture

```text
Streamlit UI
   ├─ Parsers (PDF/DOCX/URL)
   ├─ Local embeddings (fastembed MiniLM) → Supabase pgvector
   ├─ Groq LLM (analysis / rewrite / interview Qs)
   └─ Supabase Postgres + Storage
```

Embeddings and vector search run **without OpenAI**.

## Prerequisites

- Python 3.10+
- [Groq API key](https://console.groq.com/)
- [Supabase](https://supabase.com/) project

## Setup

### 1. Clone / open the project

```bash
cd AI_Resume_Analyzer
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure environment

```bash
copy .env.example .env   # Windows
# cp .env.example .env   # macOS / Linux
```

Fill in:

| Variable | Purpose |
|----------|---------|
| `GROQ_API_KEY` | Groq chat model |
| `GROQ_MODEL` | Default `llama-3.3-70b-versatile` |
| `EMBEDDING_MODEL` | Default `sentence-transformers/all-MiniLM-L6-v2` (384 dims) |
| `SUPABASE_URL` | Project URL |
| `SUPABASE_ANON_KEY` / `SUPABASE_PUBLISHABLE_KEY` | Anon / publishable key |
| `SUPABASE_SERVICE_ROLE_KEY` / `SUPABASE_SECRET_KEY` | Preferred for local demo |
| `SUPABASE_STORAGE_BUCKET` | Default `resumes` |

> **Security:** Service role bypasses RLS. Fine for a local single-user demo — do **not** expose it in a public Streamlit Cloud deploy.

### 3. Supabase database

1. Open **SQL Editor** in your Supabase project
2. Paste and run [`sql/schema.sql`](sql/schema.sql)
3. If you previously used the OpenAI 1536-dim schema, run [`sql/migrate_embeddings_384.sql`](sql/migrate_embeddings_384.sql) instead of recreating everything
4. Open **Storage** → create a private bucket named `resumes`  
   (optional second bucket: `job_descriptions`)

### 4. Run the app

```powershell
# Prefer the helper (frees port 8501, uses the project venv)
.\scripts\run_app.ps1

# Or:
.venv\Scripts\Activate.ps1
streamlit run app.py
```

Open **http://localhost:8501**. Use the sidebar: **Upload → Analyze → Edit Resume → Interview**.

## Project layout

```text
AI_Resume_Analyzer/
├── app.py
├── pages/
│   ├── 1_Upload.py
│   ├── 2_Analyze.py
│   ├── 3_Edit_Resume.py
│   └── 4_Interview.py
├── src/
│   ├── config.py
│   ├── parsers/
│   ├── rag/
│   ├── llm/
│   ├── services/
│   ├── db/
│   └── ui/
├── sql/schema.sql
├── requirements.txt
└── .env.example
```

## Demo script

1. Upload a sample resume (PDF or DOCX)
2. Paste a job description (most reliable) or try a public job URL
3. Click **Save & run analysis**
4. Review match score and skill gaps on **Analyze**
5. Generate rewrite + download PDF/DOCX on **Edit Resume**
6. Generate interview tabs on **Interview**
7. Confirm rows appear in Supabase tables: `resumes`, `job_descriptions`, `analyses`, `resume_edits`, `interview_questions`, `document_chunks`

## Notes

- Many job boards block scraping; use **Paste text** when URL fetch fails
- The rewrite prompt forbids inventing experience
- RLS policies in `schema.sql` are intentionally open for demo use only
- First embedding call downloads the ONNX model once (~80MB)

## License

MIT — for learning and portfolio use.
