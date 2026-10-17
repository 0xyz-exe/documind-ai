from pydantic import BaseModel, Field


class SearchResultResponse(BaseModel):
    chunk_id: int
    document_id: int
    document_name: str
    page_number: int | None
    text: str
    score: float


class SearchResponse(BaseModel):
    results: list[SearchResultResponse]
    total: int
    query: str
    mode: str
    latency_ms: float


class QARequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class CitationResponse(BaseModel):
    chunk_id: int
    document_id: int
    document_name: str
    page_number: int | None
    excerpt: str


class QAResponse(BaseModel):
    answer: str
    citations: list[CitationResponse]
    metadata: dict[str, str | int | float]
