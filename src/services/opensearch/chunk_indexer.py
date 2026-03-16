from opensearchpy import OpenSearch, helpers
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.paper import Paper
from src.models.paper_chunk import PaperChunk

INDEX_NAME = "paper_chunks_bm25"


def _get_client() -> OpenSearch:
    return OpenSearch(
        hosts=[{"host": "opensearch", "port": 9200}],
        use_ssl=False,
        verify_certs=False,
        ssl_show_warn=False,
    )


def reindex_all_chunks(db: Session) -> dict:
    client = _get_client()
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
                    "section_title": chunk.section_title,
                    "section_order": chunk.section_order,
                    "arxiv_id": paper.arxiv_id,
                    "title": paper.title,
                    "authors": paper.authors,
                    "published_at": paper.published_at.isoformat() if paper.published_at else None,
                },
            }
        )

    if not actions:
        return {"indexed": 0}

    success, _ = helpers.bulk(client, actions, refresh=True)
    return {"indexed": success}
