from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from ..database import Base

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, default=1)
    filename = Column(String(500), nullable=False)
    storage_path = Column(String(500), unique=True, nullable=False)
    content_type = Column(String(100), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    content_hash = Column(String(64), nullable=False, index=True)
    status = Column(String(20), nullable=False, index=True)  # uploaded, processing, indexed, failed
    page_count = Column(Integer)
    error_message = Column(Text)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    indexed_at = Column(DateTime(timezone=True))
