from pydantic import BaseModel, Field
from datetime import datetime


class SearchRequest(BaseModel):
    query: str = Field(min_length=2)
    size: int = Field(default=5, ge=1, le=20)
    author: str | None = None
    published_after: datetime | None = None


class SearchHit(BaseModel):
    paper_id: int
    arxiv_id: str
    title: str
    score: float


class SearchResponse(BaseModel):
    total: int
    hits: list[SearchHit]
