from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class DocumentResponse(BaseModel):
    id: int
    filename: str
    content_type: str
    size_bytes: int
    status: str
    page_count: Optional[int]
    uploaded_at: datetime
    indexed_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class DocumentDetail(DocumentResponse):
    content_hash: str
    chunks_count: Optional[int]
    error_message: Optional[str]
