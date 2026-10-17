import re
from dataclasses import dataclass
from math import sqrt
from typing import Iterable

from ..models.chunk import Chunk
from ..models.document import Document


@dataclass
class SearchResult:
    chunk: Chunk
    document: Document
    score: float


def _terms(value: str) -> set[str]:
    return {
        term
        for term in re.findall(r"[a-z0-9]{2,}", value.lower())
        if term not in {
            "the", "and", "for", "with", "that", "this", "are", "what",
            "is", "does", "do", "can", "how", "where", "when", "why",
        }
    }


def search_chunks(
    chunks: Iterable[tuple[Chunk, Document]],
    query: str,
    limit: int,
    mode: str = "keyword",
) -> list[SearchResult]:
    """Rank chunks locally without requiring a model download.

    The semantic mode uses a token-vector cosine score. This keeps the MVP
    deterministic and offline while leaving the service boundary ready for a
    sentence-transformers implementation later.
    """
    query_terms = _terms(query)
    if not query_terms:
        return []

    results: list[SearchResult] = []
    for chunk, document in chunks:
        terms = _terms(chunk.text)
        overlap = query_terms & terms
        if not overlap:
            continue
        if mode == "semantic":
            score = len(overlap) / sqrt(len(query_terms) * len(terms))
        else:
            score = len(overlap) / len(query_terms)
        results.append(SearchResult(chunk=chunk, document=document, score=min(score, 1.0)))

    results.sort(key=lambda result: (-result.score, result.document.filename, result.chunk.chunk_index))
    return results[:limit]
