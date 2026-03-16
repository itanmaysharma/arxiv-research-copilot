from opensearchpy import OpenSearch, helpers
from sqlalchemy import select

from src.db.session import SessionLocal
from src.models.paper import Paper
from src.models.paper_chunk import PaperChunk

INDEX_NAME = "paper_chunks_bm25"


def get_client() -> OpenSearch:
    return OpenSearch(
        hosts=[{"host": "localhost", "port": 9200}],
        use_ssl=False,
        verify_certs=False,
        ssl_show_warn=False,
    )


def main() -> None:
    client = get_client()

    with SessionLocal() as db:
        rows = db.execute(
            select(PaperChunk, Paper)
            .join(Paper, PaperChunk.paper_id == Paper.id)
            .order_by(PaperChunk.id.asc())
        ).all()

    actions = []
    for chunk, paper in rows:
        actions.append(
            {
                "_index": INDEX_NAME,
                "_id": f"{chunk.paper_id}:{chunk.chunk_index}",
                "_source": {
                    "paper_id": chunk.paper_id,
                    "chunk_index": chunk.chunk_index,
                    "chunk_text": chunk.chunk_text,
                    "arxiv_id": paper.arxiv_id,
                    "title": paper.title,
                    "authors": paper.authors,
                    "published_at": paper.published_at.isoformat() if paper.published_at else None,
                },
            }
        )

    if not actions:
        print("No chunks found.")
        return

    success, _ = helpers.bulk(client, actions, refresh=True)
    print(f"Indexed {success} chunks into '{INDEX_NAME}'.")


if __name__ == "__main__":
    main()
