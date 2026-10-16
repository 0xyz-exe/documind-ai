# Product Requirements Document — DocuMind AI

## Vision

Privacy-first document intelligence platform: ingest documents, search contents, ask questions, retrieve cited evidence, evaluate answer quality.

## Problem

Users need to extract insights from private document collections without sending data to third-party services. Existing solutions require paid APIs, lack citation integrity, or fabricate sources.

## User Personas

**Primary:** Knowledge workers managing 10-1000 documents (research papers, legal docs, technical specs, reports).

**Secondary:** Teams needing shared document workspaces with access control.

## Core User Journey

1. Create workspace
2. Upload PDF/DOCX/TXT/MD documents
3. Monitor processing status (uploaded → processing → indexed → ready)
4. Search documents (keyword + semantic)
5. Ask question in natural language
6. Receive answer with cited source passages
7. Click citation → view source document + highlighted passage
8. Ask follow-up question
9. Review retrieval history
10. Delete document (removes file, chunks, vectors)

## Functional Requirements

### P0 (MVP)

**Document Management:**
- Upload PDF, DOCX, TXT, MD (max 50MB per file)
- View document list with status
- Delete document + associated data
- Extract text with page/section metadata

**Ingestion Pipeline:**
- Validate file type, size, content
- Extract text (PyPDF2, python-docx, plain readers)
- Chunk with configurable size/overlap (500 tokens, 50 overlap default)
- Generate embeddings (local sentence-transformers model)
- Store in FAISS index
- Track status: uploaded → queued → processing → indexed → failed

**Search & Retrieval:**
- Keyword search (full-text)
- Semantic search (vector similarity, top-k=5 default)
- Return chunks with source metadata (doc, page, offset)
- Filter by document/collection

**Grounded Q&A:**
- Retrieve relevant chunks
- Generate answer using LLM (local or API)
- Validate citations (chunk IDs must exist in retrieval)
- Display answer + source excerpts
- Abstain when evidence insufficient
- Demo mode (rule-based, no API key needed)

**Workspace:**
- Single-user workspace (no auth in MVP)
- Document collection grouping
- Conversation history (scoped to workspace)

**Privacy:**
- Local-first: all processing local by default
- Optional remote LLM (explicit config)
- No telemetry, no external calls in demo mode

### P1 (Post-MVP)

- Multi-user auth (register/login)
- Workspace sharing + permissions
- OCR for scanned PDFs (pytesseract)
- Hybrid retrieval (keyword + semantic fusion)
- Reranking (cross-encoder)
- PDF viewer with citation highlighting
- Export Q&A history (JSON/CSV)

### P2 (Future)

- Additional formats (PPTX, XLSX, HTML, EPUB)
- Document versioning
- Collaborative annotations
- Custom chunking strategies
- Fine-tuned embeddings
- RAG pipeline observability dashboard

## Non-Functional Requirements

**Performance:**
- Upload: handle 50MB files
- Ingestion: < 30s for 10-page PDF
- Search: < 500ms for top-5 retrieval
- Q&A: < 10s end-to-end (local LLM)

**Security:**
- File validation (magic bytes, not extension)
- Path traversal prevention
- Size limits enforced
- No code execution from docs
- Prompt injection mitigation (system/user separation)
- Secrets server-side only

**Reliability:**
- Idempotent ingestion (retry-safe)
- Partial failure handling (don't corrupt index)
- Graceful degradation (LLM unavailable → search still works)

**Usability:**
- Clear error messages
- Processing progress visibility
- Empty states with guidance
- Mobile-responsive UI

## Acceptance Criteria

**MVP Complete When:**

1. Upload 3 PDFs (10+ pages each)
2. All reach "indexed" status
3. Keyword search returns relevant passages
4. Semantic search returns relevant passages
5. Ask question with known answer in docs
6. Receive answer with 2+ valid citations
7. Click citation → see source excerpt
8. Ask unanswerable question → get abstention response
9. Delete document → verify chunks removed
10. Run in demo mode (no API key)

**Quality Gates:**

- Ingestion: 95% success rate on valid files
- Citation validity: 100% (no invented sources)
- Retrieval latency: p95 < 1s
- Security: pass OWASP file upload checklist
- Tests: 80% coverage backend, E2E covers core journey

## Out of Scope (MVP)

- Real-time collaboration
- Mobile app
- SSO/OAuth
- Enterprise deployment
- Custom model training
- Multi-language support
- Audio/video transcription
- Web scraping
- Email integration

## Success Metrics

**Technical:**
- Ingestion success rate
- Retrieval precision@5
- Citation validity rate (citations point to real chunks)
- Answer faithfulness (to retrieved evidence)

**User:**
- Time to first answer
- Questions per session
- Citation click-through rate
- Document re-use rate

## Known Limitations

- Local embeddings: lower quality than OpenAI ada-002
- FAISS: no incremental updates (rebuild on config change)
- SQLite: single-writer bottleneck (upgrade to PostgreSQL for multi-user)
- No cross-document reasoning (retrieval per-query)
- Citation granularity: chunk-level, not sentence-level
- LLM hallucination: citations reduce but don't eliminate

## Privacy & Data Handling

**Local Processing:**
- Files stored in `storage/` directory
- Embeddings generated locally (sentence-transformers)
- Vector index local (FAISS .index file)
- No external calls in demo mode

**Optional Remote LLM:**
- User opts-in via config
- Retrieved chunks sent to API (OpenAI, etc.)
- Logged in UI before first query
- No file uploads to remote (only text chunks)

**Retention:**
- Documents: until user deletes
- Chunks/vectors: deleted with document
- Conversations: until user clears history
- No automatic backups (user-managed)

## Evaluation Strategy

**Test Datasets:**
- 10 curated docs with known Q&A pairs
- 20 questions (10 answerable, 10 not)
- Gold-standard chunk IDs for relevant passages

**Metrics:**
- Retrieval Recall@5 (chunk-level)
- Citation Precision (valid citations / total citations)
- Answer Faithfulness (LLM-as-judge: answer supported by chunks?)
- Abstention Rate (when should abstain)

**Baseline:**
- Random retrieval: ~10% Recall@5
- No-citation LLM: 0% citation precision
- Always-answer: 0% appropriate abstention

**Target (MVP):**
- Retrieval Recall@5: > 60%
- Citation Precision: 100%
- Answer Faithfulness: > 80%
- Abstention: > 50% when unanswerable

## Open Questions

1. **Chunking strategy:** Fixed-size vs. paragraph-aware? (Start fixed, benchmark both)
2. **Embedding model:** all-MiniLM-L6-v2 (fast, 384-dim) vs. all-mpnet-base-v2 (better, 768-dim)? (Start MiniLM)
3. **Context window:** How many chunks to LLM? (Start 5, tune based on latency)
4. **Reranking:** Worth the latency? (Post-MVP)
5. **PostgreSQL migration:** When? (When multi-user needed)

## Timeline (Estimated)

- **Week 1:** Milestone A (docs) + Milestone B (ingestion pipeline)
- **Week 2:** Milestone C (retrieval) + Milestone D (Q&A)
- **Week 3:** Frontend UI + integration
- **Week 4:** Milestone E (evaluation) + Milestone F (security/E2E)

---

**Status:** Approved for implementation.  
**Next:** Architecture design + database schema.
