from pydantic import BaseModel, Field


class HybridSearchRequest(BaseModel):
    query: str = Field(min_length=2)
    size: int = Field(default=5, ge=1, le=20)
    from_: int = Field(default=0, ge=0, alias="from")
    categories: list[str] | None = None
    latest_papers: bool = False
    use_hybrid: bool = True
    min_score: float = Field(default=0.0, ge=0.0)
    rrf_k: int = Field(default=60, ge=1, le=200)


class HybridSearchHit(BaseModel):
    paper_id: int
    arxiv_id: str
    title: str
    score: float
    sources: list[str]


class HybridSearchResponse(BaseModel):
    total: int
    hits: list[HybridSearchHit]
