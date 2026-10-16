# DocuMind AI

Privacy-first document intelligence platform. Upload documents, ask questions, get cited answers.

**Status:** Milestone A complete (docs), starting implementation.

## Features

- 📄 Upload PDF, DOCX, TXT, MD documents
- 🔍 Keyword + semantic search
- 💬 Q&A with source citations
- 🏠 Local-first (no external APIs required)
- 🔒 Privacy-conscious (optional remote LLM)
- ✅ Citation validation (no fake sources)

## Quick Start

### Requirements

- Python 3.11 or 3.12 (not 3.14 - limited package support)
- Node.js 18+
- Git

### Backend Setup

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
python -m app.database init
python -m app.main
```

Backend: http://localhost:8000

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend: http://localhost:3000

### Test

```bash
curl http://localhost:8000/health
```

## Architecture

- **Backend:** FastAPI, SQLAlchemy, SQLite
- **Frontend:** Next.js, React, TypeScript, Tailwind, shadcn/ui
- **Embeddings:** sentence-transformers (local)
- **Vector Search:** FAISS (local)
- **LLM:** Demo mode (default), OpenAI-compatible API (optional)

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
# Demo mode (no API key needed)
LLM_PROVIDER=demo

# Or use OpenAI-compatible API
LLM_PROVIDER=openai
LLM_API_KEY=sk-...
LLM_MODEL=gpt-4
```

## Documentation

- [PRD](docs/PRD.md) - Product requirements
- [Architecture](docs/ARCHITECTURE.md) - System design
- [Database](docs/DATABASE_DESIGN.md) - Schema
- [API](docs/API.md) - REST endpoints
- [UI/UX](docs/UI_UX_BRIEF.md) - Design specs
- [Threat Model](docs/THREAT_MODEL.md) - Security

## Project Structure

```
documind-ai/
├── backend/          # FastAPI app
│   ├── app/          # Source code
│   ├── storage/      # Uploaded files
│   └── indexes/      # FAISS indices
├── frontend/         # Next.js app
├── docs/             # Documentation
└── tests/            # E2E tests
```

## Development

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test

# E2E tests
cd tests/e2e
npx playwright test
```

## Security

- File validation (MIME type, size)
- Path traversal prevention
- Citation validation (no fake sources)
- Prompt injection mitigation
- Local-first by default

See [THREAT_MODEL.md](docs/THREAT_MODEL.md) for details.

## Privacy

**Local Mode (default):**
- All processing on your machine
- No external API calls
- Documents stay private

**Remote LLM (optional):**
- Retrieved text sent to API (not full documents)
- Explicit opt-in required
- Choose provider with no-training policy

## Roadmap

- [x] Milestone A: Documentation
- [ ] Milestone B: Document ingestion
- [ ] Milestone C: Search & retrieval
- [ ] Milestone D: Grounded Q&A
- [ ] Milestone E: Evaluation
- [ ] Milestone F: Security audit, E2E tests

## License

MIT

## Contributing

Issues and PRs welcome. See docs for architecture and conventions.

---

**Built with:** FastAPI, Next.js, sentence-transformers, FAISS
