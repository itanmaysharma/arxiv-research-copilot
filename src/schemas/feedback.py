from datetime import datetime

from pydantic import BaseModel, Field


class FeedbackCreateRequest(BaseModel):
    trace_id: str = Field(min_length=8, max_length=128)
    score: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=2000)
    channel: str = Field(default="api", min_length=2, max_length=32)


class FeedbackCreateResponse(BaseModel):
    id: int
    status: str
    trace_id: str
    created_at: datetime
