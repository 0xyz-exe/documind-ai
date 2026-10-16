# API Specification — DocuMind AI

**Base URL:** `http://localhost:8000/api/v1`  
**Format:** JSON  
**Auth:** None (MVP), JWT Bearer (P1)

## Documents

### Upload Document

```http
POST /documents
Content-Type: multipart/form-data

file: <binary>
collection_id: <integer> (optional)
```

**Response (201):**
```json
{
  "id": 1,
  "filename": "contract.pdf",
  "content_type": "application/pdf",
  "size_bytes": 1048576,
  "status": "uploaded",
  "uploaded_at": "2026-10-16T20:00:00Z"
}
```

**Errors:**
- 400: File too large, invalid type, empty
- 413: Payload too large

### List Documents

```http
GET /documents?status=indexed&limit=20&offset=0
```

**Response (200):**
```json
{
  "documents": [
    {
      "id": 1,
      "filename": "contract.pdf",
      "status": "indexed",
      "size_bytes": 1048576,
      "page_count": 10,
      "uploaded_at": "2026-10-16T20:00:00Z",
      "indexed_at": "2026-10-16T20:00:30Z"
    }
  ],
  "total": 42,
  "limit": 20,
  "offset": 0
}
```

### Get Document

```http
GET /documents/{id}
```

**Response (200):**
```json
{
  "id": 1,
  "filename": "contract.pdf",
  "content_type": "application/pdf",
  "size_bytes": 1048576,
  "content_hash": "sha256:abc...",
  "status": "indexed",
  "page_count": 10,
  "chunks_count": 25,
  "error_message": null,
  "uploaded_at": "2026-10-16T20:00:00Z",
  "indexed_at": "2026-10-16T20:00:30Z"
}
```

**Errors:**
- 404: Not found

### Download Document

```http
GET /documents/{id}/download
```

**Response (200):** Binary file with original filename

### Delete Document

```http
DELETE /documents/{id}
```

**Response (204):** No content

## Search

### Keyword Search

```http
GET /search?q=termination+clause&mode=keyword&limit=10
```

**Response (200):**
```json
{
  "results": [
    {
      "chunk_id": 42,
      "document_id": 1,
      "document_name": "contract.pdf",
      "page_number": 3,
      "text": "...termination clause...",
      "score": 0.95
    }
  ],
  "total": 5,
  "query": "termination clause",
  "mode": "keyword",
  "latency_ms": 45
}
```

### Semantic Search

```http
GET /search?q=contract+end+conditions&mode=semantic&limit=5
```

**Response:** Same as keyword, with similarity scores 0-1

## Q&A

### Ask Question

```http
POST /qa/ask
Content-Type: application/json

{
  "question": "Can the contract be terminated early?",
  "collection_id": 1,
  "conversation_id": null
}
```

**Response (200):**
```json
{
  "answer": "According to Section 5.3, the contract can be terminated with 30 days notice.",
  "citations": [
    {
      "chunk_id": 42,
      "document_id": 1,
      "document_name": "contract.pdf",
      "page_number": 3,
      "section_title": "Termination",
      "excerpt": "Either party may terminate this agreement with 30 days written notice."
    }
  ],
  "metadata": {
    "model": "gpt-4",
    "provider": "openai",
    "retrieved_chunks": 5,
    "retrieval_time_ms": 234,
    "generation_time_ms": 1567,
    "total_time_ms": 1801
  },
  "conversation_id": 5,
  "message_id": 10
}
```

**Insufficient Evidence (200):**
```json
{
  "answer": "I couldn't find enough relevant information in the documents to answer this question confidently.",
  "citations": [],
  "metadata": {...}
}
```

**Errors:**
- 400: Empty question, invalid collection_id
- 503: LLM provider unavailable

### Get Conversation History

```http
GET /qa/conversations/{id}
```

**Response (200):**
```json
{
  "id": 5,
  "title": "Can the contract be terminated early?",
  "collection_id": 1,
  "messages": [
    {
      "id": 10,
      "role": "user",
      "content": "Can the contract be terminated early?",
      "created_at": "2026-10-16T20:10:00Z"
    },
    {
      "id": 11,
      "role": "assistant",
      "content": "According to Section 5.3...",
      "metadata": {...},
      "created_at": "2026-10-16T20:10:02Z"
    }
  ],
  "created_at": "2026-10-16T20:10:00Z"
}
```

### List Conversations

```http
GET /qa/conversations?limit=10
```

**Response (200):**
```json
{
  "conversations": [
    {
      "id": 5,
      "title": "Can the contract be terminated early?",
      "collection_id": 1,
      "message_count": 4,
      "updated_at": "2026-10-16T20:15:00Z"
    }
  ],
  "total": 12
}
```

## Collections

### Create Collection

```http
POST /collections
Content-Type: application/json

{
  "name": "Contracts",
  "description": "All contract documents",
  "document_ids": [1, 2, 3]
}
```

**Response (201):**
```json
{
  "id": 1,
  "name": "Contracts",
  "description": "All contract documents",
  "document_count": 3,
  "created_at": "2026-10-16T20:00:00Z"
}
```

### List Collections

```http
GET /collections
```

**Response (200):**
```json
{
  "collections": [
    {
      "id": 1,
      "name": "Contracts",
      "document_count": 3,
      "created_at": "2026-10-16T20:00:00Z"
    }
  ]
}
```

### Update Collection

```http
PUT /collections/{id}
Content-Type: application/json

{
  "name": "Legal Contracts",
  "document_ids": [1, 2, 3, 4]
}
```

**Response (200):** Same as create

### Delete Collection

```http
DELETE /collections/{id}
```

**Response (204):** Documents not deleted, only collection

## Settings

### Get Config

```http
GET /settings/config
```

**Response (200):**
```json
{
  "embedding_model": "all-MiniLM-L6-v2",
  "embedding_device": "cpu",
  "chunk_size": 500,
  "chunk_overlap": 50,
  "top_k": 5,
  "similarity_threshold": 0.5,
  "llm_provider": "demo",
  "llm_model": null
}
```

### Update Config

```http
PUT /settings/config
Content-Type: application/json

{
  "chunk_size": 600,
  "top_k": 10
}
```

**Response (200):** Updated config  
**Warning:** Changing chunk_size requires re-indexing

## Evaluation

### Create Dataset

```http
POST /evaluation/datasets
Content-Type: application/json

{
  "name": "Contract QA",
  "questions": [
    {
      "question": "Can contract be terminated?",
      "expected_answer": "Yes, with 30 days notice",
      "relevant_document_ids": [1],
      "relevant_chunk_ids": [42]
    }
  ]
}
```

**Response (201):**
```json
{
  "id": 1,
  "name": "Contract QA",
  "question_count": 10,
  "created_at": "2026-10-16T20:00:00Z"
}
```

### Run Evaluation

```http
POST /evaluation/datasets/{id}/run
```

**Response (202):** Accepted, runs async  
**Body:**
```json
{
  "run_id": 1,
  "status": "running",
  "started_at": "2026-10-16T20:00:00Z"
}
```

### Get Evaluation Results

```http
GET /evaluation/runs/{id}
```

**Response (200):**
```json
{
  "id": 1,
  "dataset_id": 1,
  "status": "completed",
  "metrics": {
    "retrieval_recall_at_5": 0.72,
    "citation_precision": 1.0,
    "answer_faithfulness": 0.85,
    "avg_latency_ms": 1234
  },
  "config": {
    "embedding_model": "all-MiniLM-L6-v2",
    "chunk_size": 500,
    "llm_model": "gpt-4"
  },
  "completed_at": "2026-10-16T20:05:00Z"
}
```

## Health

```http
GET /health
```

**Response (200):**
```json
{
  "status": "ok",
  "database": "connected",
  "vector_index": "loaded",
  "embedding_model": "ready"
}
```

---

**Status:** Complete. Ready for implementation.
