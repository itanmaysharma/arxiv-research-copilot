from fastapi import APIRouter, Depends
from opensearchpy import OpenSearch

from src.dependencies import get_opensearch_client
from src.schemas.chunk_search import ChunkSearchHit, ChunkSearchRequest, ChunkSearchResponse
from src.services.opensearch.client import OpenSearchService

router = APIRouter(prefix="/api/v1/chunk-search", tags=["chunk-search"])


@router.post("", response_model=ChunkSearchResponse)
def chunk_search(
    request: ChunkSearchRequest,
    client: OpenSearch = Depends(get_opensearch_client),
) -> ChunkSearchResponse:
    service = OpenSearchService(client)
    resp = service.search_chunks(query=request.query, size=request.size)
    total = resp["hits"]["total"]["value"]

    hits = [
        ChunkSearchHit(
            paper_id=hit["_source"]["paper_id"],
            chunk_index=hit["_source"]["chunk_index"],
            arxiv_id=hit["_source"]["arxiv_id"],
            title=hit["_source"]["title"],
            chunk_text=hit["_source"]["chunk_text"],
            section_title=hit["_source"].get("section_title"),
            section_order=hit["_source"].get("section_order"),
            score=float(hit["_score"]),
        )
        for hit in resp["hits"]["hits"]
    ]
    return ChunkSearchResponse(total=total, hits=hits)
