from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(min_length=3)
    top_k: int = Field(default=3, ge=1, le=10)


class AskResponse(BaseModel):
    answer: str
    sources: list[dict]
    search_mode: str
    retrieval_attempts: int
    confidence: float
    citations: list[str]
