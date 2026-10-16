from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pathlib import Path
import uuid
from datetime import datetime

from .config import settings
from .database import get_db, init_db
from .models import Document
from .schemas.document import DocumentResponse
from .services.validation import validate_file, compute_hash, safe_filename
from .services.extraction import extract_text, ExtractionError
from .services.chunking import chunk_text
from .models.chunk import Chunk as ChunkModel

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

@app.get("/api/v1/documents/{doc_id}", response_model=DocumentResponse)
def get_document(doc_id: int, db: Session = Depends(get_db)):
    """Get document details"""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

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
