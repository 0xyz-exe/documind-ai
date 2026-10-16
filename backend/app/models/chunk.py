from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from ..database import Base

class Chunk(Base):
    __tablename__ = "chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    page_number = Column(Integer)
    section_title = Column(String(500))
    start_offset = Column(Integer)
    end_offset = Column(Integer)
    token_count = Column(Integer)
    embedding_index = Column(Integer, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
