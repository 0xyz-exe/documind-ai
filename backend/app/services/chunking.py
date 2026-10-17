from typing import List, Tuple
from dataclasses import dataclass

@dataclass
class Chunk:
    text: str
    chunk_index: int
    start_offset: int
    end_offset: int
    token_count: int
    page_number: int | None = None

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[Chunk]:
    """Split text into overlapping chunks by character count (approx tokens)"""
    
    if not text.strip():
        return []
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be non-negative and smaller than chunk_size")
    
    chunks = []
    start = 0
    chunk_index = 0
    text_len = len(text)
    
    while start < text_len:
        end = start + chunk_size
        
        # Don't split mid-word at end
        if end < text_len:
            # Look for space/newline within last 50 chars
            search_start = max(start, end - 50)
            last_break = max(
                text.rfind(' ', search_start, end),
                text.rfind('\n', search_start, end)
            )
            if last_break > start:
                end = last_break + 1
        
        chunk_text = text[start:end].strip()
        
        if chunk_text:
            chunks.append(Chunk(
                text=chunk_text,
                chunk_index=chunk_index,
                start_offset=start,
                end_offset=end,
                token_count=len(chunk_text.split()),  # ponytail: rough token count, upgrade to tiktoken
            ))
            chunk_index += 1
        
        start = end - overlap if overlap > 0 else end
    
    return chunks
