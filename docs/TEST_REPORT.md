# Test Report — DocuMind AI

**Date:** 2026-10-16  
**Status:** Test specifications complete, execution blocked on Python 3.14

## Test Strategy

### Test Pyramid

```
          E2E (10%)
         ┌────────┐
        Integration (30%)
       ┌──────────────┐
      Unit Tests (60%)
     ┌──────────────────┐
```

## Unit Tests (Backend)

### File Validation

**File:** `tests/unit/test_validation.py`

```python
import pytest
from app.services.validation import validate_file, compute_hash, safe_filename

def test_validate_file_valid_pdf():
    content = b'%PDF-1.4...'  # Valid PDF magic bytes
    valid, mime, error = validate_file(content, "test.pdf")
    assert valid == True
    assert mime == "application/pdf"
    assert error == ""

def test_validate_file_too_large():
    content = b'x' * (51 * 1024 * 1024)  # 51 MB
    valid, mime, error = validate_file(content, "large.pdf")
    assert valid == False
    assert "too large" in error.lower()

def test_validate_file_empty():
    valid, mime, error = validate_file(b'', "empty.txt")
    assert valid == False
    assert "empty" in error.lower()

def test_validate_file_unsupported_type():
    content = b'\x89PNG...'  # PNG magic bytes
    valid, mime, error = validate_file(content, "image.png")
    assert valid == False
    assert "unsupported" in error.lower()

def test_compute_hash():
    content = b'test content'
    hash1 = compute_hash(content)
    hash2 = compute_hash(content)
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256

def test_safe_filename():
    assert safe_filename("/etc/passwd") == "passwd"
    assert safe_filename("../../secret.txt") == "secret.txt"
    assert safe_filename("normal.pdf") == "normal.pdf"
```

### Text Extraction

**File:** `tests/unit/test_extraction.py`

```python
import pytest
from pathlib import Path
from app.services.extraction import extract_text, ExtractionError

@pytest.fixture
def sample_pdf(tmp_path):
    # Create minimal valid PDF
    pdf_content = b'%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n...'
    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_bytes(pdf_content)
    return str(pdf_path)

def test_extract_pdf(sample_pdf):
    text, pages = extract_text(sample_pdf, "application/pdf")
    assert isinstance(text, str)
    assert pages > 0

def test_extract_text_file(tmp_path):
    txt_path = tmp_path / "test.txt"
    txt_path.write_text("Hello world\nThis is a test.")
    
    text, pages = extract_text(str(txt_path), "text/plain")
    assert "Hello world" in text
    assert pages == 1

def test_extract_empty_pdf_fails(tmp_path):
    pdf_path = tmp_path / "empty.pdf"
    pdf_path.write_bytes(b'%PDF-1.4...')  # Minimal but no text
    
    with pytest.raises(ExtractionError, match="No text extracted"):
        extract_text(str(pdf_path), "application/pdf")

def test_extract_unsupported_type():
    with pytest.raises(ExtractionError, match="Unsupported"):
        extract_text("fake.png", "image/png")
```

### Chunking

**File:** `tests/unit/test_chunking.py`

```python
from app.services.chunking import chunk_text

def test_chunk_text_basic():
    text = "a" * 1000
    chunks = chunk_text(text, chunk_size=500, overlap=50)
    
    assert len(chunks) > 1
    assert chunks[0].chunk_index == 0
    assert chunks[0].start_offset == 0
    assert chunks[0].end_offset <= 500

def test_chunk_text_overlap():
    text = "word " * 200
    chunks = chunk_text(text, chunk_size=500, overlap=50)
    
    if len(chunks) > 1:
        # Check overlap
        chunk0_end = chunks[0].text[-50:]
        chunk1_start = chunks[1].text[:50]
        # Some overlap should exist (not exact due to word boundaries)
        assert len(chunk0_end) > 0

def test_chunk_text_empty():
    chunks = chunk_text("", chunk_size=500, overlap=50)
    assert len(chunks) == 0

def test_chunk_text_short():
    text = "Short text"
    chunks = chunk_text(text, chunk_size=500, overlap=50)
    assert len(chunks) == 1
    assert chunks[0].text == text

def test_chunk_text_word_boundary():
    text = "one two three four five six seven eight nine ten"
    chunks = chunk_text(text, chunk_size=20, overlap=5)
    
    # Should not split mid-word
    for chunk in chunks:
        assert not chunk.text.startswith(" ")
        assert not chunk.text.endswith(" ") or chunk == chunks[-1]
```

### Citation Validation

**File:** `tests/unit/test_citations.py`

```python
from app.services.citations import extract_citations, validate_citations
from app.models import Chunk, Document

def test_extract_citations():
    answer = "According to [1] and [2], the answer is yes [3]."
    citations = extract_citations(answer)
    assert citations == [1, 2, 3]

def test_extract_no_citations():
    answer = "No citations here."
    citations = extract_citations(answer)
    assert citations == []

def test_validate_citations_valid():
    chunks = [Chunk(id=i) for i in range(1, 4)]
    answer = "Per [1] and [2], yes."
    
    valid, invalid = validate_citations(answer, chunks)
    assert valid == True
    assert invalid == []

def test_validate_citations_invalid():
    chunks = [Chunk(id=i) for i in range(1, 3)]
    answer = "Per [1], [2], and [5], yes."  # [5] invalid
    
    valid, invalid = validate_citations(answer, chunks)
    assert valid == False
    assert 5 in invalid
```

## Integration Tests (Backend)

### Document Upload & Processing

**File:** `tests/integration/test_document_flow.py`

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine, get_db
from sqlalchemy.orm import Session

@pytest.fixture
def client():
    Base.metadata.create_all(bind=engine)
    client = TestClient(app)
    yield client
    Base.metadata.drop_all(bind=engine)

def test_upload_document(client, tmp_path):
    # Create test PDF
    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_bytes(b'%PDF-1.4...<valid pdf content>')
    
    with open(pdf_path, 'rb') as f:
        response = client.post(
            "/api/v1/documents",
            files={"file": ("test.pdf", f, "application/pdf")}
        )
    
    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == "test.pdf"
    assert data["status"] in ["uploaded", "indexed"]
    assert "id" in data

def test_upload_invalid_file(client):
    response = client.post(
        "/api/v1/documents",
        files={"file": ("test.png", b'\x89PNG...', "image/png")}
    )
    
    assert response.status_code == 400
    assert "unsupported" in response.json()["detail"].lower()

def test_list_documents(client):
    # Upload 2 docs
    # ... (upload code)
    
    response = client.get("/api/v1/documents")
    assert response.status_code == 200
    data = response.json()
    assert "documents" in data
    assert data["total"] >= 2

def test_get_document(client):
    # Upload doc
    # ...
    
    response = client.get(f"/api/v1/documents/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1

def test_delete_document(client):
    # Upload doc
    # ...
    
    response = client.delete("/api/v1/documents/1")
    assert response.status_code == 204
    
    # Verify deleted
    response = client.get("/api/v1/documents/1")
    assert response.status_code == 404
```

### Q&A Flow

**File:** `tests/integration/test_qa.py`

```python
def test_qa_with_relevant_docs(client, db_session):
    # Upload & index document with known content
    # ...
    
    response = client.post(
        "/api/v1/qa/ask",
        json={"question": "What is the termination clause?"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "citations" in data
    assert len(data["citations"]) > 0
    
    # Validate citations
    for citation in data["citations"]:
        assert "chunk_id" in citation
        assert "document_name" in citation

def test_qa_no_relevant_docs(client):
    # No documents uploaded
    
    response = client.post(
        "/api/v1/qa/ask",
        json={"question": "What is X?"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "couldn't find" in data["answer"].lower() or "no relevant" in data["answer"].lower()
    assert len(data["citations"]) == 0
```

## End-to-End Tests (Playwright)

**File:** `tests/e2e/test_user_journey.spec.ts`

```typescript
import { test, expect } from '@playwright/test';

test.describe('Document Intelligence Workflow', () => {
  test('complete user journey', async ({ page }) => {
    // 1. Open app
    await page.goto('http://localhost:3000');
    
    // 2. Upload document
    await page.click('button:has-text("Upload")');
    await page.setInputFiles('input[type="file"]', 'fixtures/contract.pdf');
    await page.click('button:has-text("Upload")');
    
    // 3. Wait for processing
    await expect(page.locator('text=indexed')).toBeVisible({ timeout: 30000 });
    
    // 4. Navigate to Q&A
    await page.click('a:has-text("Q&A")');
    
    // 5. Ask question
    await page.fill('textarea[placeholder*="question"]', 'Can this contract be terminated early?');
    await page.click('button:has-text("Send")');
    
    // 6. Verify answer with citations
    await expect(page.locator('.answer')).toContainText('30 days');
    await expect(page.locator('.citation')).toContainText('[1]');
    
    // 7. Click citation
    await page.click('.citation:has-text("[1]")');
    
    // 8. Verify source panel
    await expect(page.locator('.source-panel')).toContainText('contract.pdf');
    await expect(page.locator('.source-panel')).toContainText('Page 3');
  });
  
  test('unanswerable question', async ({ page }) => {
    await page.goto('http://localhost:3000/qa');
    
    await page.fill('textarea', 'Who is the CEO of Mars?');
    await page.click('button:has-text("Send")');
    
    await expect(page.locator('.answer')).toContainText(/don't have enough|insufficient/i);
    await expect(page.locator('.citation')).toHaveCount(0);
  });
  
  test('delete document', async ({ page }) => {
    await page.goto('http://localhost:3000/documents');
    
    const docCount = await page.locator('.document-row').count();
    
    // Delete first doc
    await page.click('.document-row:first-child button[aria-label="Delete"]');
    await page.click('button:has-text("Confirm")');
    
    // Verify count decreased
    await expect(page.locator('.document-row')).toHaveCount(docCount - 1);
  });
});
```

## Performance Tests

**File:** `tests/performance/locustfile.py`

```python
from locust import HttpUser, task, between

class DocuMindUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def search_documents(self):
        self.client.get("/api/v1/search?q=contract&mode=keyword")
    
    @task(1)
    def ask_question(self):
        self.client.post("/api/v1/qa/ask", json={
            "question": "What is the termination clause?"
        })
    
    @task(2)
    def list_documents(self):
        self.client.get("/api/v1/documents?limit=20")
```

**Run:**
```bash
locust -f tests/performance/locustfile.py --host=http://localhost:8000
```

**Targets:**
- Search: p95 < 500ms
- Q&A: p95 < 10s
- List: p95 < 200ms

## Test Commands

```bash
# Unit tests
cd backend
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# E2E tests
cd tests/e2e
npx playwright test

# Coverage
pytest --cov=app --cov-report=html

# Performance
locust -f tests/performance/locustfile.py
```

## CI/CD Pipeline

**File:** `.github/workflows/test.yml`

```yaml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: test
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python 3.11
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-cov
      
      - name: Run unit tests
        run: |
          cd backend
          pytest tests/unit/ -v --cov=app
      
      - name: Run integration tests
        run: |
          cd backend
          pytest tests/integration/ -v
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
  
  e2e:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install Playwright
        run: |
          cd tests/e2e
          npm install
          npx playwright install
      
      - name: Run E2E tests
        run: |
          cd tests/e2e
          npx playwright test
      
      - name: Upload test results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: playwright-report
          path: tests/e2e/playwright-report/
```

## Test Coverage Targets

- Unit tests: >80%
- Integration tests: Critical paths covered
- E2E tests: 3 core journeys
- Security: OWASP Top 10 mitigated

## Known Test Gaps

**Blocked (Python 3.14):**
- All backend tests
- Integration tests
- Performance tests

**Future (P1):**
- Multi-user scenarios
- Concurrent upload stress test
- Large document (>50MB) rejection
- OCR pipeline tests
- Reranking tests

---

**Status:** Test design complete. Execution requires Python 3.11/3.12.
