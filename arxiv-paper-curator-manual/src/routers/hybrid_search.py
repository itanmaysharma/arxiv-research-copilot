from fastapi import APIRouter, Depends
from opensearchpy import OpenSearch

from src.dependencies import get_embeddings_client, get_opensearch_client
from src.schemas.hybrid_search import (
    HybridSearchRequest,
    HybridSearchResponse,
)
from src.services.embeddings.jina_client import JinaEmbeddingsClient
from src.services.indexing.hybrid_indexer import rrf_fuse
from src.services.opensearch.client import OpenSearchService

router = APIRouter(prefix="/api/v1/hybrid-search", tags=["hybrid-search"])


@router.post("", response_model=HybridSearchResponse)
def hybrid_search(
    request: HybridSearchRequest,
    client: OpenSearch = Depends(get_opensearch_client),
    embedder: JinaEmbeddingsClient = Depends(get_embeddings_client),
) -> HybridSearchResponse:
    service = OpenSearchService(client)

    keyword_hits = service.search_keyword_chunks(
        query=request.query,
        size=request.size,
        from_=request.from_,
        categories=request.categories,
        latest_papers=request.latest_papers,
    )

    vector_hits: list[dict] = []
    if request.use_hybrid:
        try:
            query_embedding = embedder.embed_query(request.query)
            vector_hits = service.search_vector_chunks(
                query_embedding=query_embedding,
                size=request.size,
                categories=request.categories,
            )
        except Exception:
            # Keep the endpoint available even when vector setup is missing.
            vector_hits = []

    fused_hits = rrf_fuse(
        keyword_hits=keyword_hits,
        vector_hits=vector_hits,
        k=request.rrf_k,
        min_score=request.min_score,
    )

    top = fused_hits[: request.size]
    return HybridSearchResponse(total=len(top), hits=top)
