from pydantic import BaseModel, Field


class AgenticAskRequest(BaseModel):
    question: str = Field(min_length=3)
    top_k: int = Field(default=3, ge=1, le=10)


class AgenticStep(BaseModel):
    node: str
    status: str
    detail: str


class AgenticAskResponse(BaseModel):
    answer: str
    steps: list[AgenticStep]
    sources: list[dict]
    search_mode: str
    retrieval_attempts: int
    confidence: float
    citations: list[str]
