from pydantic import BaseModel, Field


class ChunkSearchRequest(BaseModel):
    query: str = Field(min_length=2)
    size: int = Field(default=5, ge=1, le=20)


class ChunkSearchHit(BaseModel):
    paper_id: int
    chunk_index: int
    arxiv_id: str
    title: str
    chunk_text: str
    section_title: str | None = None
    section_order: int | None = None
    score: float


class ChunkSearchResponse(BaseModel):
    total: int
    hits: list[ChunkSearchHit]
