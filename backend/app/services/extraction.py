from pypdf import PdfReader
from docx import Document as DocxDocument
from typing import Tuple, Optional
from pathlib import Path

class ExtractionError(Exception):
    pass

def extract_text(file_path: str, content_type: str) -> Tuple[str, Optional[int]]:
    """Extract text from document. Returns (text, page_count)"""
    
    try:
        if content_type == "application/pdf":
            return _extract_pdf(file_path)
        elif content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return _extract_docx(file_path)
        elif content_type in ("text/plain", "text/markdown"):
            return _extract_text(file_path)
        else:
            raise ExtractionError(f"Unsupported content type: {content_type}")
    except Exception as e:
        raise ExtractionError(f"Extraction failed: {str(e)}")

def _extract_pdf(file_path: str) -> Tuple[str, int]:
    """Extract text from PDF"""
    reader = PdfReader(file_path)
    pages = []
    
    for page in reader.pages:
        text = page.extract_text()
        if text.strip():
            pages.append(text)
    
    if not pages:
        raise ExtractionError("No text extracted from PDF")
    
    return "\n\n".join(pages), len(reader.pages)

def _extract_docx(file_path: str) -> Tuple[str, int]:
    """Extract text from DOCX"""
    doc = DocxDocument(file_path)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    
    if not paragraphs:
        raise ExtractionError("No text extracted from DOCX")
    
    # Approximate page count (250 words per page)
    word_count = sum(len(p.split()) for p in paragraphs)
    page_count = max(1, word_count // 250)
    
    return "\n\n".join(paragraphs), page_count

def _extract_text(file_path: str) -> Tuple[str, int]:
    """Extract text from TXT/MD"""
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        text = f.read()
    
    if not text.strip():
        raise ExtractionError("Empty text file")
    
    # Approximate page count
    line_count = text.count('\n')
    page_count = max(1, line_count // 50)
    
    return text, page_count
