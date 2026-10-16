# Repository Audit

**Date:** 2026-10-16  
**Status:** Greenfield

## Existing State

Empty repository. No prior code, dependencies, or technical debt.

## Recommended Stack

**Backend:**
- Python 3.11/3.12 + FastAPI
- SQLite (local MVP) → PostgreSQL (multi-user)
- SQLAlchemy ORM
- Pydantic validation

**Frontend:**
- Next.js 14+ (App Router)
- React 18+
- TypeScript
- Tailwind CSS + shadcn/ui

**Document Processing:**
- PyPDF2 / pypdf (PDF text)
- python-docx (DOCX)
- Built-in (TXT, MD)
- pytesseract (OCR, optional)

**Embeddings & Vector Search:**
- sentence-transformers (local embeddings)
- FAISS (local vector index)
- Optional: pgvector if PostgreSQL

**LLM:**
- Provider-agnostic interface
- Local: llama-cpp-python (optional)
- Remote: OpenAI-compatible API (optional)
- Demo: rule-based stub (no API key)

**Testing:**
- pytest (backend)
- Vitest (frontend)
- Playwright (E2E)

## Implementation Order

**Milestone A:** Docs (PRD, architecture, threat model)  
**Milestone B:** Document ingestion (upload, parse, chunk, store)  
**Milestone C:** Search & retrieval (keyword + semantic)  
**Milestone D:** Grounded Q&A (citations, providers)  
**Milestone E:** Evaluation framework  
**Milestone F:** Security audit, E2E tests

## Security Concerns

- File upload validation (type, size, content)
- Path traversal in storage
- Prompt injection in retrieved docs
- SSRF if URL fetch added
- Authorization at retrieval layer
- Secret exposure in logs/frontend

## Dependencies

- Python 3.11+ (avoid 3.14, limited package support)
- Node.js 18+
- Git
- Optional: Tesseract OCR
- Optional: GPU for local LLM
