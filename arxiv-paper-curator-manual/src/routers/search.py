from fastapi import APIRouter, Depends
from opensearchpy import OpenSearch
from src.schemas.search import SearchHit, SearchRequest, SearchResponse
from sqlalchemy.orm import Session
from src.dependencies import get_db, get_opensearch_client
from src.services.opensearch.client import OpenSearchService
from src.services.opensearch.indexer import reindex_all_papers

router = APIRouter(prefix="/api/v1/search", tags=["search"])

@router.post("", response_model=SearchResponse)
def search(
    request: SearchRequest,
    client: OpenSearch = Depends(get_opensearch_client),
) -> SearchResponse:
    service = OpenSearchService(client)
    resp = service.search_papers(
        query=request.query,
        size=request.size,
        author=request.author,
        published_after=request.published_after.isoformat() if request.published_after else None,
    )
    total = resp["hits"]["total"]["value"]
    hits = [
        SearchHit(
            paper_id=hit["_source"]["paper_id"],
            arxiv_id=hit["_source"]["arxiv_id"],
            title=hit["_source"]["title"],
            score=float(hit["_score"]),
        )
        for hit in resp["hits"]["hits"]
    ]
    return SearchResponse(total=total, hits=hits)

@router.post("/reindex")
def reindex(db: Session = Depends(get_db)) -> dict:
    return reindex_all_papers(db)
