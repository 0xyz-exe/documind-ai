import hashlib
import magic
from pathlib import Path
from typing import Tuple

ALLOWED_TYPES = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "text/plain": ".txt",
    "text/markdown": ".md",
}

MAX_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB

def validate_file(content: bytes, filename: str) -> Tuple[bool, str, str]:
    """Validate file content and type. Returns (valid, content_type, error_msg)"""
    
    # Size check
    if len(content) > MAX_SIZE_BYTES:
        return False, "", f"File too large: {len(content)} bytes (max {MAX_SIZE_BYTES})"
    
    if len(content) == 0:
        return False, "", "Empty file"
    
    # MIME type check (magic bytes, not extension)
    mime = magic.from_buffer(content, mime=True)
    
    # Allow text/plain for .md files
    if filename.endswith(".md") and mime == "text/plain":
        mime = "text/markdown"
    
    if mime not in ALLOWED_TYPES:
        return False, "", f"Unsupported file type: {mime}"
    
    return True, mime, ""

def compute_hash(content: bytes) -> str:
    """Compute SHA-256 hash of file content"""
    return hashlib.sha256(content).hexdigest()

def safe_filename(filename: str) -> str:
    """Remove path components, keep only basename"""
    return Path(filename).name
