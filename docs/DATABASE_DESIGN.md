# Database Design — DocuMind AI

## Database Selection

**MVP:** SQLite (local, zero-config, sufficient for single-user)  
**Production:** PostgreSQL 14+ (multi-user, pgvector for embeddings)

## Schema

### Users (P1, multi-user)

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
```

### Workspaces (P1, multi-user)

```sql
CREATE TABLE workspaces (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    owner_id INTEGER NOT NULL,
    settings JSON,  -- embedding_model, chunk_size, llm_config
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_workspaces_owner ON workspaces(owner_id);
```

### Documents

```sql
CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workspace_id INTEGER DEFAULT 1,  -- Default workspace for single-user MVP
    filename VARCHAR(500) NOT NULL,
    storage_path VARCHAR(500) UNIQUE NOT NULL,
    content_type VARCHAR(100) NOT NULL,
    size_bytes INTEGER NOT NULL,
    content_hash VARCHAR(64) NOT NULL,  -- SHA-256 for dedup
    status VARCHAR(20) NOT NULL,  -- uploaded, queued, processing, indexed, failed
    page_count INTEGER,
    error_message TEXT,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    indexed_at TIMESTAMP,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
);

CREATE INDEX idx_documents_workspace ON documents(workspace_id);
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_documents_hash ON documents(content_hash);
```

**Status values:**
- `uploaded`: File saved, pending processing
- `queued`: In processing queue (future: task queue)
- `processing`: Text extraction in progress
- `indexed`: Fully processed, chunks in DB, vectors in FAISS
- `failed`: Processing error (see error_message)

### Collections

```sql
CREATE TABLE collections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workspace_id INTEGER DEFAULT 1,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
);

CREATE INDEX idx_collections_workspace ON collections(workspace_id);
```

### Collection_Documents (Many-to-Many)

```sql
CREATE TABLE collection_documents (
    collection_id INTEGER NOT NULL,
    document_id INTEGER NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (collection_id, document_id),
    FOREIGN KEY (collection_id) REFERENCES collections(id) ON DELETE CASCADE,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);

CREATE INDEX idx_collection_docs_collection ON collection_documents(collection_id);
CREATE INDEX idx_collection_docs_document ON collection_documents(document_id);
```

### Chunks

```sql
CREATE TABLE chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    chunk_index INTEGER NOT NULL,  -- Order within document
    text TEXT NOT NULL,
    page_number INTEGER,  -- Null if not applicable (TXT, MD)
    section_title VARCHAR(500),  -- If document has structure
    start_offset INTEGER,  -- Character offset in original document
    end_offset INTEGER,
    token_count INTEGER,
    embedding_index INTEGER,  -- Position in FAISS index
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);

CREATE INDEX idx_chunks_document ON chunks(document_id);
CREATE INDEX idx_chunks_embedding_index ON chunks(embedding_index);

-- Full-text search (SQLite FTS5 for keyword search)
CREATE VIRTUAL TABLE chunks_fts USING fts5(
    chunk_id UNINDEXED,
    text,
    content=chunks,
    content_rowid=id
);

-- Triggers to keep FTS in sync
CREATE TRIGGER chunks_ai AFTER INSERT ON chunks BEGIN
    INSERT INTO chunks_fts(rowid, chunk_id, text) VALUES (new.id, new.id, new.text);
END;

CREATE TRIGGER chunks_ad AFTER DELETE ON chunks BEGIN
    DELETE FROM chunks_fts WHERE rowid = old.id;
END;

CREATE TRIGGER chunks_au AFTER UPDATE ON chunks BEGIN
    UPDATE chunks_fts SET text = new.text WHERE rowid = new.id;
END;
```

**Note:** Embeddings stored in FAISS index file, not DB. `embedding_index` is the position in FAISS (0, 1, 2, ...).

### Conversations

```sql
CREATE TABLE conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workspace_id INTEGER DEFAULT 1,
    collection_id INTEGER,  -- Null = all documents
    title VARCHAR(500),  -- First question, truncated
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE,
    FOREIGN KEY (collection_id) REFERENCES collections(id) ON DELETE SET NULL
);

CREATE INDEX idx_conversations_workspace ON conversations(workspace_id);
CREATE INDEX idx_conversations_updated ON conversations(updated_at DESC);
```

### Messages

```sql
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL,
    role VARCHAR(20) NOT NULL,  -- user, assistant
    content TEXT NOT NULL,
    metadata JSON,  -- retrieval_time_ms, model, token_count, citations
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);

CREATE INDEX idx_messages_conversation ON messages(conversation_id);
```

**metadata JSON example (assistant messages):**
```json
{
  "model": "gpt-4",
  "provider": "openai",
  "retrieval_time_ms": 234,
  "generation_time_ms": 1567,
  "retrieved_chunks": 5,
  "citations": [
    {"chunk_id": 42, "document_id": 5, "page": 3}
  ]
}
```

### Retrieval_Events (Optional, for debugging/analytics)

```sql
CREATE TABLE retrieval_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id INTEGER,
    query_text TEXT NOT NULL,
    method VARCHAR(50),  -- keyword, semantic, hybrid
    top_k INTEGER,
    similarity_threshold REAL,
    retrieved_chunk_ids TEXT,  -- JSON array: [1, 5, 9, ...]
    latency_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE
);

CREATE INDEX idx_retrieval_message ON retrieval_events(message_id);
```

### Evaluation_Datasets

```sql
CREATE TABLE evaluation_datasets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workspace_id INTEGER DEFAULT 1,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
);
```

### Evaluation_Questions

```sql
CREATE TABLE evaluation_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dataset_id INTEGER NOT NULL,
    question TEXT NOT NULL,
    expected_answer TEXT,  -- Optional reference answer
    relevant_document_ids TEXT,  -- JSON array
    relevant_chunk_ids TEXT,  -- JSON array (for recall calculation)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (dataset_id) REFERENCES evaluation_datasets(id) ON DELETE CASCADE
);

CREATE INDEX idx_eval_questions_dataset ON evaluation_questions(dataset_id);
```

### Evaluation_Runs

```sql
CREATE TABLE evaluation_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dataset_id INTEGER NOT NULL,
    config_snapshot JSON NOT NULL,  -- embedding_model, chunk_size, llm_model, top_k
    metrics JSON,  -- recall, precision, faithfulness
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (dataset_id) REFERENCES evaluation_datasets(id) ON DELETE CASCADE
);

CREATE INDEX idx_eval_runs_dataset ON evaluation_runs(dataset_id);
```

### Evaluation_Results (Per-question results)

```sql
CREATE TABLE evaluation_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    question_id INTEGER NOT NULL,
    retrieved_chunk_ids TEXT,  -- JSON array
    recall REAL,  -- If gold chunk IDs provided
    answer TEXT,
    citations_valid BOOLEAN,
    faithfulness_score REAL,  -- 0-1, LLM-as-judge
    latency_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (run_id) REFERENCES evaluation_runs(id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES evaluation_questions(id) ON DELETE CASCADE
);

CREATE INDEX idx_eval_results_run ON evaluation_results(run_id);
```

## Relationships

```
users 1───N workspaces
workspaces 1───N documents
workspaces 1───N collections
workspaces 1───N conversations
workspaces 1───N evaluation_datasets

documents 1───N chunks
documents N───N collections (via collection_documents)

collections 1───N conversations (optional filter)

conversations 1───N messages
messages 1───1 retrieval_events (optional)

evaluation_datasets 1───N evaluation_questions
evaluation_datasets 1───N evaluation_runs
evaluation_runs 1───N evaluation_results
evaluation_results N───1 evaluation_questions
```

## Data Lifecycle

### Document Deletion

**Cascade:**
1. Delete document record
2. Delete all chunks (ON DELETE CASCADE)
3. Delete FTS entries (trigger)
4. Remove FAISS vectors (manual: rebuild index or mark stale)
5. Delete file from storage/
6. Remove from collection_documents

**Implementation:** Soft delete (status=deleted) or hard delete? → Hard delete for MVP (GDPR compliance).

### Conversation Retention

**Options:**
- Keep forever (default)
- Auto-delete after N days (configurable)
- User-initiated clear history

### Index Rebuild

**Triggers:**
- Chunking config change
- Embedding model change
- Manual re-index

**Process:**
1. Mark all documents status=queued
2. Re-extract and chunk
3. Re-embed
4. Rebuild FAISS index from scratch
5. Update embedding_index in chunks

## Migrations (Alembic)

### Initial Migration

```python
# alembic/versions/001_initial_schema.py
def upgrade():
    # Create all tables
    op.create_table('documents', ...)
    op.create_table('chunks', ...)
    # ...
    op.execute('CREATE VIRTUAL TABLE chunks_fts ...')

def downgrade():
    op.drop_table('chunks_fts')
    op.drop_table('chunks')
    op.drop_table('documents')
```

### Future: Add Users/Workspaces

```python
# alembic/versions/002_add_multiuser.py
def upgrade():
    op.create_table('users', ...)
    op.create_table('workspaces', ...)
    # Migrate existing documents to default workspace
    op.add_column('documents', sa.Column('workspace_id', sa.Integer, server_default='1'))
```

## PostgreSQL Differences

### UUID Primary Keys (Optional)

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    -- ...
);
```

### pgvector for Embeddings (P1)

```sql
CREATE EXTENSION vector;

ALTER TABLE chunks ADD COLUMN embedding vector(384);  -- 384 for MiniLM, 768 for mpnet

CREATE INDEX idx_chunks_embedding ON chunks USING ivfflat (embedding vector_cosine_ops);
```

**Query:**
```sql
SELECT id, 1 - (embedding <=> query_embedding) AS similarity
FROM chunks
ORDER BY embedding <=> query_embedding
LIMIT 5;
```

**Note:** pgvector slower than FAISS for <100k vectors, but simpler (no separate index file).

### Full-Text Search (PostgreSQL)

```sql
ALTER TABLE chunks ADD COLUMN text_tsvector tsvector;

CREATE INDEX idx_chunks_text_search ON chunks USING gin(text_tsvector);

-- Auto-update trigger
CREATE TRIGGER chunks_text_search_update BEFORE INSERT OR UPDATE
ON chunks FOR EACH ROW EXECUTE FUNCTION
tsvector_update_trigger(text_tsvector, 'pg_catalog.english', text);

-- Query
SELECT * FROM chunks WHERE text_tsvector @@ plainto_tsquery('search query');
```

## Indexes Summary

**Critical for Performance:**
- `documents.workspace_id` (multi-user filtering)
- `documents.status` (processing queue)
- `chunks.document_id` (document deletion)
- `chunks.embedding_index` (FAISS lookup)
- `chunks_fts` (keyword search)
- `messages.conversation_id` (conversation history)
- `conversations.updated_at DESC` (recent conversations)

## Storage Estimates

**Per document (10-page PDF):**
- File: 1 MB
- Chunks (20 chunks x 500 chars): 10 KB in DB
- Embeddings (20 x 384 x 4 bytes): 30 KB in FAISS
- Metadata: ~1 KB

**Total per doc:** ~1.04 MB

**For 1000 documents:**
- Storage: 1 GB
- Database: 11 MB
- FAISS index: 30 MB

**SQLite limits:** 281 TB (not a concern for MVP)

## Backup Strategy

**SQLite:**
- Copy `.db` file (when app stopped, or use `VACUUM INTO`)
- Copy `storage/` directory
- Copy `indexes/` directory

**PostgreSQL:**
- `pg_dump` (logical backup)
- WAL archiving (point-in-time recovery)

## Testing Data

**Seed script (for development):**
- 10 sample documents (mixed PDF/DOCX/TXT)
- 3 collections
- 20 Q&A pairs
- 1 evaluation dataset (10 questions)

**Reset script:**
```bash
rm documind.db storage/* indexes/*
alembic upgrade head
python seed.py
```

---

**Status:** Approved for implementation.  
**Next:** Threat model + API specification.
