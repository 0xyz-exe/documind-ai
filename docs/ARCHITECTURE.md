# Architecture — DocuMind AI

## Overview

**Type:** Monorepo (frontend + backend in one repo)  
**Deployment:** Local-first (single-user), optional multi-user deployment  
**Stack:** Next.js frontend, FastAPI backend, SQLite/PostgreSQL, FAISS vector index

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Document    │  │   Q&A        │  │   Settings   │      │
│  │  Library     │  │   Workspace  │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└────────────────────────┬────────────────────────────────────┘
                         │ REST API (HTTP)
┌────────────────────────▼────────────────────────────────────┐
│                     Backend (FastAPI)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   API        │  │   Ingestion  │  │   RAG        │      │
│  │   Routes     │  │   Pipeline   │  │   Engine     │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │              │
│  ┌──────▼──────────────────▼──────────────────▼───────┐    │
│  │              Services Layer                          │    │
│  │  (Auth, Documents, Chunking, Embeddings, Retrieval,│    │
│  │   LLM, Citations, Evaluation)                       │    │
│  └──────┬──────────────────┬──────────────────┬────────┘    │
│         │                  │                  │              │
│  ┌──────▼───────┐   ┌──────▼───────┐  ┌──────▼───────┐    │
│  │  PostgreSQL/ │   │  File        │  │  FAISS       │    │
│  │  SQLite      │   │  Storage     │  │  Vector      │    │
│  │  (metadata)  │   │  (originals) │  │  Index       │    │
│  └──────────────┘   └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## Technology Stack

### Frontend
- **Framework:** Next.js 14+ (App Router)
- **Language:** TypeScript 5+
- **UI Library:** React 18+
- **Styling:** Tailwind CSS 3+
- **Components:** shadcn/ui (Radix UI primitives)
- **State:** React hooks (local state), fetch/SWR (server state)
- **PDF Viewer:** react-pdf or pdf.js
- **HTTP Client:** fetch (native) with error handling wrapper

### Backend
- **Framework:** FastAPI 0.104+
- **Language:** Python 3.11/3.12
- **ASGI Server:** Uvicorn
- **ORM:** SQLAlchemy 2.0+
- **Validation:** Pydantic 2.0+
- **Migrations:** Alembic
- **Task Queue:** None (MVP: sync processing) → Future: Celery/RQ

### Database
- **MVP:** SQLite (local, single-user)
- **Production:** PostgreSQL 14+ (multi-user, with pgvector extension)

### Document Processing
- **PDF:** PyPDF2 or pypdf
- **DOCX:** python-docx
- **TXT/MD:** Built-in Python readers
- **OCR (P1):** pytesseract + Tesseract engine

### Embeddings
- **Library:** sentence-transformers
- **Default Model:** all-MiniLM-L6-v2 (384-dim, fast)
- **Alternative:** all-mpnet-base-v2 (768-dim, better quality)
- **Device:** CPU (default) or CUDA (if available)

### Vector Search
- **Library:** FAISS (Facebook AI Similarity Search)
- **Index Type:** IndexFlatIP (inner product, exact search)
- **Persistence:** Save/load .index files to disk

### LLM Providers
- **Demo Mode:** Rule-based stub (pattern matching, no API)
- **Local:** llama-cpp-python (optional, requires model download)
- **Remote:** OpenAI API or compatible (OpenRouter, local LLM server)
- **Interface:** Abstract provider class (swappable)

### Testing
- **Backend:** pytest, pytest-asyncio
- **Frontend:** Vitest, React Testing Library
- **E2E:** Playwright
- **Coverage:** pytest-cov, c8

### DevOps
- **Version Control:** Git
- **CI:** GitHub Actions (on push: lint, test, build)
- **Containerization:** Docker (optional, for deployment)
- **Environment:** .env files (python-dotenv)

## Project Structure

```
documind-ai/
├── frontend/
│   ├── app/                # Next.js App Router pages
│   │   ├── page.tsx        # Dashboard
│   │   ├── documents/      # Document library
│   │   ├── qa/             # Q&A workspace
│   │   └── settings/       # Settings
│   ├── components/         # React components
│   │   ├── ui/             # shadcn/ui components
│   │   ├── documents/      # Document-specific
│   │   └── qa/             # Q&A-specific
│   ├── lib/                # Utils, API client
│   ├── hooks/              # Custom React hooks
│   ├── public/             # Static assets
│   ├── styles/             # Global CSS
│   ├── package.json
│   ├── tsconfig.json
│   └── next.config.js
├── backend/
│   ├── app/
│   │   ├── main.py         # FastAPI app, routes
│   │   ├── config.py       # Settings (pydantic-settings)
│   │   ├── database.py     # SQLAlchemy setup
│   │   ├── models/         # SQLAlchemy models
│   │   │   ├── user.py
│   │   │   ├── document.py
│   │   │   ├── chunk.py
│   │   │   ├── conversation.py
│   │   │   └── ...
│   │   ├── schemas/        # Pydantic schemas (request/response)
│   │   ├── routes/         # API route modules
│   │   │   ├── documents.py
│   │   │   ├── qa.py
│   │   │   ├── search.py
│   │   │   └── ...
│   │   ├── services/       # Business logic
│   │   │   ├── ingestion.py
│   │   │   ├── chunking.py
│   │   │   ├── embeddings.py
│   │   │   ├── retrieval.py
│   │   │   ├── llm.py
│   │   │   ├── citations.py
│   │   │   └── evaluation.py
│   │   ├── providers/      # LLM provider implementations
│   │   │   ├── base.py
│   │   │   ├── demo.py
│   │   │   ├── openai.py
│   │   │   └── local.py
│   │   └── security/       # Validation, auth
│   ├── storage/            # Uploaded files (gitignored)
│   ├── indexes/            # FAISS index files (gitignored)
│   ├── alembic/            # Database migrations
│   ├── tests/              # Backend tests
│   ├── requirements.txt
│   └── pyproject.toml      # Optional (Poetry/PDM)
├── tests/
│   └── e2e/                # Playwright tests
├── docs/                   # Documentation (this file)
├── .gitignore
├── .env.example
├── README.md
└── docker-compose.yml      # Optional
```

## Data Flow

### Document Ingestion

```
1. User uploads file (frontend)
   ↓
2. POST /api/v1/documents (multipart/form-data)
   ↓
3. Backend validates (type, size, content)
   ↓
4. Save file to storage/ with generated ID
   ↓
5. Create Document record (status=uploaded)
   ↓
6. Extract text (PyPDF2/python-docx)
   ↓
7. Update status=processing
   ↓
8. Chunk text (chunking service)
   ↓
9. Generate embeddings (sentence-transformers)
   ↓
10. Store chunks in DB, add vectors to FAISS index
   ↓
11. Update status=indexed
   ↓
12. Return Document response to frontend
```

### Question Answering

```
1. User asks question (frontend)
   ↓
2. POST /api/v1/qa/ask {"question": "...", "collection_id": 123}
   ↓
3. Backend retrieves relevant chunks:
   a. Embed question (same model as docs)
   b. FAISS vector search (top-k=5)
   c. Optional: keyword search (SQLite FTS)
   d. Optional: reranking (cross-encoder)
   ↓
4. Build LLM context:
   - System prompt (grounding instructions)
   - Retrieved chunks (with metadata)
   - Question
   ↓
5. Call LLM provider (demo/local/remote)
   ↓
6. Parse response, extract citations
   ↓
7. Validate citations (chunk IDs exist in retrieval)
   ↓
8. Save conversation message (question + answer + citations)
   ↓
9. Return Answer response:
   {
     "answer": "...",
     "citations": [
       {"chunk_id": 1, "document_id": 5, "page": 3, "excerpt": "..."}
     ],
     "sources": [...],
     "metadata": {"latency_ms": 1234, "model": "gpt-4"}
   }
   ↓
10. Frontend renders answer with citation badges
```

### Search

```
1. User enters query (frontend)
   ↓
2. GET /api/v1/search?q=...&mode=keyword|semantic
   ↓
3. Backend:
   - If keyword: SQLite full-text search on chunk.text
   - If semantic: Embed query, FAISS search
   ↓
4. Return matching chunks with metadata
   ↓
5. Frontend displays results (grouped by document)
```

## Security Architecture

### Authentication (P1, multi-user)
- **Mechanism:** JWT tokens (httpOnly cookies)
- **Flow:** Register → Login → JWT issued → Stored in cookie
- **Middleware:** FastAPI dependency validates JWT on protected routes

### Authorization
- **Model:** User → Workspace → Documents
- **Enforcement:** Every document/chunk retrieval checks workspace ownership
- **DB:** Foreign keys: Document.workspace_id, User.id

### Input Validation
- **File Upload:**
  - MIME type check (magic bytes, not extension)
  - Size limit (50 MB)
  - Content scan (no code execution)
- **API:**
  - Pydantic schemas validate all inputs
  - SQL injection: Parameterized queries (SQLAlchemy)
  - XSS: Sanitize output (automatic in React)

### Prompt Injection Mitigation
- **System/User Separation:** LLM prompts clearly separate system instructions from user/document content
- **Citation Validation:** Server-side check that citations reference real chunks
- **Output Filtering:** Strip control characters, limit length

### File Storage
- **Location:** Outside web root (storage/ directory)
- **Naming:** Generated UUIDs, not user-provided names
- **Retrieval:** Validate document ownership before serving file

### Secrets Management
- **API Keys:** Stored server-side only (.env file)
- **Never:** Sent to frontend, logged, or committed to git

## Scalability Considerations

### MVP (Single-User)
- **Database:** SQLite (sufficient for <10k documents)
- **Vector Index:** FAISS in-memory (loaded on startup)
- **Processing:** Synchronous (acceptable for <100 docs)

### Multi-User (P1)
- **Database:** PostgreSQL (concurrent writes)
- **Vector Index:** pgvector extension (or separate FAISS per workspace)
- **Processing:** Async task queue (Celery + Redis)
- **Caching:** Redis (embeddings, search results)

### Large-Scale (Future)
- **Search:** Elasticsearch or Meilisearch
- **Vectors:** Weaviate, Qdrant, or Pinecone
- **Storage:** S3/MinIO for documents
- **Compute:** Distributed workers (Kubernetes)

## Configuration

### Environment Variables (.env)

```bash
# Database
DATABASE_URL=sqlite:///./documind.db  # or postgresql://...

# Storage
STORAGE_DIR=./storage
INDEX_DIR=./indexes

# Embeddings
EMBEDDING_MODEL=all-MiniLM-L6-v2
EMBEDDING_DEVICE=cpu  # or cuda

# Chunking
CHUNK_SIZE=500
CHUNK_OVERLAP=50

# Retrieval
TOP_K=5
SIMILARITY_THRESHOLD=0.5

# LLM
LLM_PROVIDER=demo  # demo, local, openai
LLM_API_KEY=sk-...  # if openai
LLM_API_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4
LLM_MAX_TOKENS=1000
LLM_TEMPERATURE=0.1

# Server
BACKEND_PORT=8000
FRONTEND_PORT=3000
ALLOWED_ORIGINS=http://localhost:3000

# Security
SECRET_KEY=<generate-random-key>
JWT_EXPIRY_HOURS=24

# Feature Flags
ENABLE_OCR=false
ENABLE_RERANKING=false
```

### Dynamic Configuration (P1)
- User-level settings stored in DB (workspace.settings JSON column)
- Override env defaults per workspace

## Error Handling

### Backend
- **Exceptions:** Custom exception classes (DocumentProcessingError, RetrievalError, etc.)
- **HTTP Responses:** Structured error JSON:
  ```json
  {
    "error": "document_too_large",
    "message": "File exceeds 50 MB limit",
    "details": {"size_mb": 75, "limit_mb": 50}
  }
  ```
- **Logging:** Python logging module (INFO for normal, ERROR for failures)

### Frontend
- **API Errors:** Catch fetch errors, display toast notifications
- **Boundary:** React Error Boundary for component crashes
- **Fallback:** Show error page with home link

## Monitoring & Observability (P1)

### Metrics
- **Ingestion:** Success rate, avg latency per file type
- **Retrieval:** Latency (p50, p95, p99), cache hit rate
- **LLM:** Latency, token usage, error rate
- **DB:** Query latency, connection pool usage

### Logging
- **Structured:** JSON logs (timestamp, level, service, message, context)
- **Retention:** 30 days (rotate daily)
- **PII Redaction:** No user content in logs (only IDs)

### Tracing (Future)
- **OpenTelemetry:** Instrument FastAPI + Next.js
- **Spans:** Upload → Extract → Chunk → Embed → Index

## Deployment

### Local (MVP)
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev  # http://localhost:3000
```

### Docker (Optional)
```yaml
# docker-compose.yml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    env_file: .env
    volumes:
      - ./storage:/app/storage
      - ./indexes:/app/indexes
  
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
```

### Production (P1)
- **Backend:** Gunicorn + Uvicorn workers, behind nginx
- **Frontend:** Next.js production build (npm run build), served by nginx or Vercel
- **Database:** Managed PostgreSQL (RDS, Supabase, etc.)
- **Storage:** S3 or equivalent
- **SSL:** Let's Encrypt or Cloudflare

## Testing Strategy

### Unit Tests (Backend)
- **Services:** Chunking, embeddings, citations (mocked dependencies)
- **Utilities:** File validation, URL parsing
- **Models:** SQLAlchemy CRUD operations

### Integration Tests (Backend)
- **API Routes:** Full request/response cycle
- **Database:** Test DB (separate SQLite or PostgreSQL)
- **FAISS:** Test index creation, search

### Unit Tests (Frontend)
- **Components:** Render, interactions (Vitest + React Testing Library)
- **Hooks:** Custom hooks behavior
- **Utils:** API client, formatting

### E2E Tests (Playwright)
- **Happy Path:** Upload → Search → Ask → Cite → Delete
- **Error Paths:** Invalid file, LLM failure, no results
- **Auth (P1):** Register → Login → Protected routes

### Performance Tests (P1)
- **Load:** Concurrent uploads, queries (Locust)
- **Benchmarks:** Embedding latency, retrieval latency

## Migration Strategy (SQLite → PostgreSQL)

1. **Schema Parity:** Alembic migrations work for both
2. **Data Export:** SQLite dump → PostgreSQL import (or ETL script)
3. **Vector Index:** Rebuild from chunks (or migrate to pgvector)
4. **Config:** Change DATABASE_URL, restart

---

**Status:** Approved for implementation.  
**Next:** Database design + API specification.
