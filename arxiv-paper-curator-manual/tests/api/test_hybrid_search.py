from unittest.mock import patch

from src.dependencies import get_embeddings_client, get_opensearch_client
from src.main import app


class DummyEmbedder:
    def embed_query(self, query: str) -> list[float]:
        assert query
        return [0.1, 0.2, 0.3]


def test_hybrid_search_uses_keyword_and_vector(client):
    keyword_hits = [
        {
            "_source": {
                "paper_id": 10,
                "arxiv_id": "2603.06485v1",
                "title": "PONTE",
            }
        }
    ]
    vector_hits = [
        {
            "_source": {
                "paper_id": 10,
                "arxiv_id": "2603.06485v1",
                "title": "PONTE",
            }
        }
    ]

    app.dependency_overrides[get_opensearch_client] = lambda: object()
    app.dependency_overrides[get_embeddings_client] = lambda: DummyEmbedder()
    with (
        patch("src.routers.hybrid_search.OpenSearchService.search_keyword_chunks", return_value=keyword_hits),
        patch("src.routers.hybrid_search.OpenSearchService.search_vector_chunks", return_value=vector_hits),
    ):
        try:
            response = client.post(
                "/api/v1/hybrid-search",
                json={
                    "query": "preference vectors",
                    "size": 3,
                    "from": 1,
                    "categories": ["2603.06485v1"],
                    "latest_papers": True,
                    "use_hybrid": True,
                    "min_score": 0.0,
                },
            )
        finally:
            app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["hits"][0]["paper_id"] == 10
    assert payload["hits"][0]["sources"] == ["bm25", "vector"]


def test_hybrid_search_falls_back_when_vector_fails(client):
    keyword_hits = [
        {
            "_source": {
                "paper_id": 11,
                "arxiv_id": "2603.00001v1",
                "title": "Fallback",
            }
        }
    ]

    app.dependency_overrides[get_opensearch_client] = lambda: object()
    app.dependency_overrides[get_embeddings_client] = lambda: DummyEmbedder()
    with (
        patch("src.routers.hybrid_search.OpenSearchService.search_keyword_chunks", return_value=keyword_hits),
        patch(
            "src.routers.hybrid_search.OpenSearchService.search_vector_chunks",
            side_effect=RuntimeError("vector unavailable"),
        ),
    ):
        try:
            response = client.post("/api/v1/hybrid-search", json={"query": "fallback", "size": 3})
        finally:
            app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["hits"][0]["paper_id"] == 11
    assert payload["hits"][0]["sources"] == ["bm25"]


def test_hybrid_search_bm25_only_mode(client):
    keyword_hits = [
        {"_source": {"paper_id": 99, "arxiv_id": "2603.09999v1", "title": "BM25 Only"}}
    ]

    app.dependency_overrides[get_opensearch_client] = lambda: object()
    app.dependency_overrides[get_embeddings_client] = lambda: DummyEmbedder()
    with (
        patch("src.routers.hybrid_search.OpenSearchService.search_keyword_chunks", return_value=keyword_hits),
        patch("src.routers.hybrid_search.OpenSearchService.search_vector_chunks") as mock_vector,
    ):
        try:
            response = client.post(
                "/api/v1/hybrid-search",
                json={"query": "bm25 mode", "size": 3, "use_hybrid": False},
            )
        finally:
            app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["hits"][0]["paper_id"] == 99
    assert payload["hits"][0]["sources"] == ["bm25"]
    mock_vector.assert_not_called()
