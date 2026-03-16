from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.session import SessionLocal
from src.models.paper import Paper
from src.services.arxiv.client import ArxivClient


def parse_published(value: str) -> datetime | None:
    if not value:
        return None
    # arXiv returns e.g. 2026-03-08T00:00:00Z
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def upsert_paper(db: Session, item) -> tuple[str, Paper]:
    existing = db.execute(select(Paper).where(Paper.arxiv_id == item.arxiv_id)).scalar_one_or_none()
    if existing:
        existing.title = item.title
        existing.abstract = item.abstract
        existing.authors = item.authors
        existing.pdf_url = item.pdf_url
        existing.published_at = parse_published(item.published_at)
        return "updated", existing

    new_paper = Paper(
        arxiv_id=item.arxiv_id,
        title=item.title,
        abstract=item.abstract,
        authors=item.authors,
        pdf_url=item.pdf_url,
        full_text=None,
        published_at=parse_published(item.published_at),
    )
    db.add(new_paper)
    return "created", new_paper


def main() -> None:
    client = ArxivClient(delay_seconds=0.5)
    papers = client.fetch(query="cat:cs.AI", max_results=5)

    created = 0
    updated = 0

    with SessionLocal() as db:
        for item in papers:
            action, _ = upsert_paper(db, item)
            if action == "created":
                created += 1
            else:
                updated += 1
        db.commit()

    print(f"Ingestion complete. created={created}, updated={updated}, fetched={len(papers)}")


if __name__ == "__main__":
    main()
