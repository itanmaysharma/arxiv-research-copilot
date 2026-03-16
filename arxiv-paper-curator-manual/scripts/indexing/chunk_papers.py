from sqlalchemy import delete, select

from src.db.session import SessionLocal
from src.models.paper import Paper
from src.models.paper_chunk import PaperChunk
from src.services.indexing.text_chunker import TextChunker


def main() -> None:
    chunker = TextChunker(chunk_size=800, overlap=120)

    total_papers = 0
    total_chunks = 0

    with SessionLocal() as db:
        papers = db.execute(select(Paper).order_by(Paper.id.asc())).scalars().all()

        for paper in papers:
            source_text = paper.full_text or paper.abstract
            if not source_text:
                continue

            chunks = chunker.chunk_text(source_text)

            db.execute(delete(PaperChunk).where(PaperChunk.paper_id == paper.id))

            for c in chunks:
                db.add(
                    PaperChunk(
                        paper_id=paper.id,
                        chunk_index=c.chunk_id,
                        chunk_text=c.text,
                        start_char=c.start_char,
                        end_char=c.end_char,
                    )
                )

            total_papers += 1
            total_chunks += len(chunks)

        db.commit()

    print(f"Chunking complete. papers={total_papers}, chunks={total_chunks}")


if __name__ == "__main__":
    main()
