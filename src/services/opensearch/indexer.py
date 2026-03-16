from opensearchpy import OpenSearch, helpers
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.paper import Paper

INDEX_NAME = "papers_bm25"


def _get_client() -> OpenSearch:
    return OpenSearch(
        hosts=[{"host": "opensearch", "port": 9200}],
        use_ssl=False,
        verify_certs=False,
        ssl_show_warn=False,
    )


def reindex_all_papers(db: Session) -> dict:
    client = _get_client()
    papers = db.execute(select(Paper).order_by(Paper.id.asc())).scalars().all()

    actions = []
    for p in papers:
        actions.append(
            {
                "_index": INDEX_NAME,
                "_id": str(p.id),
                "_source": {
                    "paper_id": p.id,
                    "arxiv_id": p.arxiv_id,
                    "title": p.title,
                    "abstract": p.abstract,
                    "authors": p.authors,
                    "published_at": p.published_at.isoformat() if p.published_at else None,
                    "pdf_url": p.pdf_url,
                },
            }
        )

    if not actions:
        return {"indexed": 0}

    success, _ = helpers.bulk(client, actions, refresh=True)
    return {"indexed": success}
