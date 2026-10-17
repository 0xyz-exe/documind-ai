from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pathlib import Path
import uuid
from datetime import datetime
from time import perf_counter

from .config import settings
from .database import get_db, init_db
from .models import Document
from .schemas.document import DocumentResponse, DocumentDetail
from .schemas.qa import (
    CitationResponse,
    QARequest,
    QAResponse,
    SearchResponse,
    SearchResultResponse,
)
from .services.validation import validate_file, compute_hash, safe_filename
from .services.extraction import extract_text, ExtractionError
from .services.chunking import chunk_text
from .models.chunk import Chunk as ChunkModel
from .services.retrieval import search_chunks

app = FastAPI(title="DocuMind AI", version="0.1.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize on startup
@app.on_event("startup")
def startup():
    init_db()
    Path(settings.storage_dir).mkdir(exist_ok=True)
    Path(settings.index_dir).mkdir(exist_ok=True)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/api/v1/documents", response_model=DocumentResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload and process document"""
    
    # Read file content
    content = await file.read()
    filename = safe_filename(file.filename or "unknown")
    
    # Validate
    valid, content_type, error = validate_file(content, filename)
    if not valid:
        raise HTTPException(status_code=400, detail=error)
    
    # Check for duplicate (by hash)
    content_hash = compute_hash(content)
    existing = db.query(Document).filter(Document.content_hash == content_hash).first()
    if existing:
        raise HTTPException(status_code=400, detail="Document already exists")
    
    # Save file
    storage_id = str(uuid.uuid4())
    storage_path = Path(settings.storage_dir) / f"{storage_id}.bin"
    storage_path.write_bytes(content)
    
    # Create document record
    doc = Document(
        filename=filename,
        storage_path=str(storage_path),
        content_type=content_type,
        size_bytes=len(content),
        content_hash=content_hash,
        status="uploaded"
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    
    # Process synchronously (MVP: no async queue)
    try:
        doc.status = "processing"
        db.commit()
        
        # Extract text
        text, page_count = extract_text(str(storage_path), content_type)
        doc.page_count = page_count
        
        # Chunk
        chunks = chunk_text(text, settings.chunk_size, settings.chunk_overlap)
        
        # Save chunks
        for chunk in chunks:
            chunk_model = ChunkModel(
                document_id=doc.id,
                chunk_index=chunk.chunk_index,
                text=chunk.text,
                start_offset=chunk.start_offset,
                end_offset=chunk.end_offset,
                token_count=chunk.token_count,
            )
            db.add(chunk_model)
        
        doc.status = "indexed"
        doc.indexed_at = datetime.utcnow()
        db.commit()
        db.refresh(doc)
        
    except ExtractionError as e:
        doc.status = "failed"
        doc.error_message = str(e)
        db.commit()
        db.refresh(doc)
    
    return doc

@app.get("/api/v1/documents")
def list_documents(
    status: str | None = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """List documents"""
    query = db.query(Document)
    
    if status:
        query = query.filter(Document.status == status)
    
    total = query.count()
    docs = query.order_by(Document.uploaded_at.desc()).offset(offset).limit(limit).all()
    
    return {
        "documents": docs,
        "total": total,
        "limit": limit,
        "offset": offset
    }

@app.get("/api/v1/documents/{doc_id}", response_model=DocumentDetail)
def get_document(doc_id: int, db: Session = Depends(get_db)):
    """Get document details"""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return {
        **{field: getattr(doc, field) for field in (
            "id", "filename", "content_type", "size_bytes", "status",
            "page_count", "uploaded_at", "indexed_at", "content_hash",
            "error_message",
        )},
        "chunks_count": db.query(ChunkModel).filter(ChunkModel.document_id == doc.id).count(),
    }


@app.get("/api/v1/documents/{doc_id}/download")
def download_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    storage_path = Path(doc.storage_path)
    if not storage_path.is_file():
        raise HTTPException(status_code=404, detail="Stored document is missing")
    return FileResponse(storage_path, filename=doc.filename, media_type=doc.content_type)


@app.get("/api/v1/search", response_model=SearchResponse)
def search_documents(
    q: str,
    mode: str = "keyword",
    limit: int = 10,
    db: Session = Depends(get_db),
):
    if not q.strip():
        raise HTTPException(status_code=400, detail="Search query cannot be empty")
    if mode not in {"keyword", "semantic"}:
        raise HTTPException(status_code=400, detail="Mode must be keyword or semantic")
    if not 1 <= limit <= 100:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")

    started = perf_counter()
    rows = (
        db.query(ChunkModel, Document)
        .join(Document, ChunkModel.document_id == Document.id)
        .filter(Document.status == "indexed")
        .all()
    )
    matches = search_chunks(rows, q, limit, mode)
    return SearchResponse(
        results=[
            SearchResultResponse(
                chunk_id=result.chunk.id,
                document_id=result.document.id,
                document_name=result.document.filename,
                page_number=result.chunk.page_number,
                text=result.chunk.text,
                score=round(result.score, 4),
            )
            for result in matches
        ],
        total=len(matches),
        query=q,
        mode=mode,
        latency_ms=round((perf_counter() - started) * 1000, 2),
    )


@app.post("/api/v1/qa/ask", response_model=QAResponse)
def ask_question(request: QARequest, db: Session = Depends(get_db)):
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    started = perf_counter()
    rows = (
        db.query(ChunkModel, Document)
        .join(Document, ChunkModel.document_id == Document.id)
        .filter(Document.status == "indexed")
        .all()
    )
    matches = search_chunks(rows, question, settings.top_k, "keyword")
    if not matches or matches[0].score < settings.similarity_threshold:
        answer = "I couldn't find enough relevant information in the documents to answer this question confidently."
        citations: list[CitationResponse] = []
    else:
        selected = matches[:3]
        answer = "Based on the uploaded documents: " + " ".join(
            result.chunk.text.splitlines()[0].strip() for result in selected
        )
        citations = [
            CitationResponse(
                chunk_id=result.chunk.id,
                document_id=result.document.id,
                document_name=result.document.filename,
                page_number=result.chunk.page_number,
                excerpt=result.chunk.text[:500],
            )
            for result in selected
        ]

    return QAResponse(
        answer=answer,
        citations=citations,
        metadata={
            "provider": settings.llm_provider,
            "model": settings.llm_model if settings.llm_provider != "demo" else "demo",
            "retrieved_chunks": len(matches),
            "total_time_ms": round((perf_counter() - started) * 1000, 2),
        },
    )

@app.delete("/api/v1/documents/{doc_id}", status_code=204)
def delete_document(doc_id: int, db: Session = Depends(get_db)):
    """Delete document and associated data"""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete file
    storage_path = Path(doc.storage_path)
    if storage_path.exists():
        storage_path.unlink()
    
    # Delete chunks (cascade)
    db.delete(doc)
    db.commit()
    
    return None

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.backend_port)
