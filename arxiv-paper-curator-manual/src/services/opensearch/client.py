from opensearchpy import OpenSearch

from src.services.opensearch.query_builder import (
    build_chunk_search_query,
    build_keyword_chunk_search_query,
    build_paper_search_query,
    build_vector_chunk_search_query,
)

PAPERS_INDEX_NAME = "papers_bm25"
CHUNKS_INDEX_NAME = "paper_chunks_bm25"
VECTOR_CHUNKS_INDEX_NAME = "paper_chunks_vector"


class OpenSearchService:
    def __init__(self, client: OpenSearch) -> None:
        self.client = client

    def search_papers(
        self,
        query: str,
        size: int,
        author: str | None = None,
        published_after: str | None = None,
    ) -> dict:
        body = build_paper_search_query(
            query=query,
            size=size,
            author=author,
            published_after=published_after,
        )
        return self.client.search(index=PAPERS_INDEX_NAME, body=body)

    def search_chunks(self, query: str, size: int) -> dict:
        body = build_chunk_search_query(query=query, size=size)
        return self.client.search(index=CHUNKS_INDEX_NAME, body=body)

    def search_keyword_chunks(
        self,
        query: str,
        size: int,
        from_: int = 0,
        categories: list[str] | None = None,
        latest_papers: bool = False,
    ) -> list[dict]:
        body = build_keyword_chunk_search_query(
            query=query,
            size=size,
            from_=from_,
            categories=categories,
            latest_papers=latest_papers,
        )
        resp = self.client.search(index=CHUNKS_INDEX_NAME, body=body)
        return resp["hits"]["hits"]

    def search_vector_chunks(
        self,
        query_embedding: list[float],
        size: int,
        categories: list[str] | None = None,
    ) -> list[dict]:
        body = build_vector_chunk_search_query(
            query_embedding=query_embedding,
            size=size,
            categories=categories,
        )
        resp = self.client.search(index=VECTOR_CHUNKS_INDEX_NAME, body=body)
        return resp["hits"]["hits"]
