from datetime import datetime

from sqlalchemy import DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base


class Paper(Base):
    __tablename__ = "papers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    arxiv_id: Mapped[str] = mapped_column(Text, unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    abstract: Mapped[str] = mapped_column(Text, nullable=False)
    authors: Mapped[str] = mapped_column(Text, nullable=False)
    pdf_url: Mapped[str] = mapped_column(Text, nullable=False)
    full_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    parser_metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
