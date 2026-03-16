from datetime import datetime

from pydantic import BaseModel, Field


class PaperCreate(BaseModel):
    arxiv_id: str = Field(min_length=3)
    title: str = Field(min_length=3)
    abstract: str = Field(min_length=3)
    authors: str = Field(min_length=1)
    pdf_url: str = Field(min_length=5)
    full_text: str | None = None
    published_at: datetime | None = None


class PaperOut(BaseModel):
    id: int
    arxiv_id: str
    title: str
    authors: str
    published_at: datetime | None = None


class PaperCreateResponse(BaseModel):
    id: int
    arxiv_id: str
    status: str
