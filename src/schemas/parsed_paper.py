from pydantic import BaseModel, Field


class ParsedReference(BaseModel):
    label: str | None = None
    raw_text: str = Field(min_length=1)


class ParsedSection(BaseModel):
    title: str = Field(min_length=1)
    text: str = Field(min_length=1)
    order: int = Field(ge=1)


class ParsedDocument(BaseModel):
    full_text: str = ""
    sections: list[ParsedSection] = []
    references: list[ParsedReference] = []
    metadata: dict = {}
