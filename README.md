# DocuMind

AI-Powered Contextual Document Finder. Hybrid semantic + BM25 retrieval over local files, external drives, scanned documents (OCR), and public YouTube transcripts.

## Repo Layout

```
DocuMind/
├── backend/          # FastAPI + Celery (Python 3.11, uv)
├── frontend/         # Next.js 15 + Tailwind + TanStack Query (TypeScript)
├── docker-compose.yml
└── README.md
```

## Backend Status — Phases B1 – B7 complete

| Phase | Coverage |
|---|---|
| B1 | FastAPI skeleton, async SQLAlchemy/SQLite, Celery + Redis, logging, /health |
| B2 | Upload + recursive directory ingest, MIME/exe validation, dedup via SHA-256, extractors (PDF/DOCX/TXT/CSV/XLSX/PPTX) |
| B3 | Tesseract OCR for images and scanned PDFs; YouTube transcript ingestion with yt-dlp + youtube-transcript-api |
| B4 | LlamaIndex semantic chunking, sentence-transformers (BAAI/bge-large-en-v1.5) embeddings, Qdrant vector store, OpenSearch BM25 store, heuristic title/keyword/summary extractors |
| B5 | Hybrid retrieval (RRF fusion of vector + BM25), BAAI/bge-reranker-large reranking, snippet highlighting (`<mark>` wrapping) with multi-snippet support |
| B6 | Redis query cache (30-min TTL), archive/unarchive/reindex/delete endpoints |
| B7 | Latency middleware (X-Response-Time-Ms), health probes for Redis/Qdrant/OpenSearch |

## Frontend Status — F1–F5 complete

- Next.js 15 App Router + TypeScript + Tailwind v3 (light/dark/system theme)
- TanStack Query for server state with auto-polling on in-flight jobs
- Pages: **Search**, **Ingest**, **Files**
- Search: hybrid query bar, faceted filters (file type / source / folder prefix / archived), result cards with `<mark>`-rendered snippets, YouTube timestamps + deep links
- Ingest: drag-drop multi-upload, server-side directory scan, YouTube URL submission
- Files: paginated table, status + source filters, archive / unarchive / reindex / delete with confirm dialog, detail drawer
- Sonner toasts, lucide icons, live dependency health badge in the header

## Quick Start (Docker)

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
docker compose up --build
```

- Frontend: http://localhost:3000
- API: http://localhost:8000 — interactive docs at http://localhost:8000/docs

First search request will download embedding (~1.3 GB) and reranker (~1.1 GB) models into the `hf-cache` volume.

## Local dev — Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev    # http://localhost:3000
```

## Local dev — Backend

```bash
cd backend
uv sync
cp .env.example .env

# Required services (or `docker compose up redis qdrant opensearch`)
redis-server &
# Qdrant + OpenSearch via compose recommended

# API
uv run uvicorn app.main:app --reload

# Worker (in another shell)
uv run celery -A app.workers.celery_app.celery_app worker --loglevel=info
```

System packages needed for local dev (Ubuntu/Debian):

```bash
sudo apt-get install -y tesseract-ocr poppler-utils libmagic1 ffmpeg
```

## API Reference

| Method | Path | Purpose |
|---|---|---|
| GET    | `/health` | Liveness + downstream dependency status |
| POST   | `/upload` | Upload a single file; queues full ingestion |
| GET    | `/files` | List files (paginated, filterable by status/source_type) |
| POST   | `/ingest/directory` | Recursively scan a directory, queue ingestion for each file |
| POST   | `/youtube/index` | Submit public YouTube URL, queue transcript ingestion |
| POST   | `/search` | Hybrid search; returns ranked files with highlighted snippets |
| POST   | `/archive/{id}` | Archive a file (excluded from default search) |
| POST   | `/unarchive/{id}` | Restore an archived file |
| POST   | `/reindex/{id}` | Re-run the full ingestion pipeline for a file |
| DELETE | `/file/{id}` | Permanently delete file + vectors + BM25 + blob |

### Search request shape

```jsonc
POST /search
{
  "query": "how does the indexing pipeline handle scanned PDFs?",
  "top_k": 10,
  "filters": {
    "file_types": ["pdf", "docx"],
    "directory_prefix": "engineering/specs",
    "source_types": ["upload", "directory"],
    "include_archived": false
  }
}
```

Response includes `cached`, `elapsed_ms`, and per-result `snippets` each carrying `text`, `highlighted` (with `<mark>...</mark>`), `score`, and (for YouTube) `start_seconds` / `end_seconds`.

## Tests

```bash
cd backend
uv run pytest
```

## Tech Stack (FRD §7)

- **Backend:** FastAPI, Celery, Redis
- **AI:** LlamaIndex, sentence-transformers, BAAI/bge-large-en-v1.5, BAAI/bge-reranker-large
- **Stores:** Qdrant (vectors), OpenSearch (BM25), SQLite/SQLAlchemy (file + chunk registry)
- **OCR:** Tesseract via pytesseract + pdf2image (poppler)
- **YouTube:** yt-dlp, youtube-transcript-api
- **Infra:** Docker, Docker Compose

## Out of scope (per FRD §1.3)

Google Drive, multi-user auth, cloud deployment, direct video uploads, real-time collaboration, LLM answer synthesis.
