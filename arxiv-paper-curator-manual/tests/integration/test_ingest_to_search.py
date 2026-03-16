from types import SimpleNamespace
from unittest.mock import patch

from src.dependencies import get_db, get_opensearch_client
from src.main import app


class DummyOSClient:
    def search(self, index, body):
        assert index == "papers_bm25"
        assert "query" in body
        return {
            "hits": {
                "total": {"value": 1},
                "hits": [
                    {
                        "_score": 8.7,
                        "_source": {
                            "paper_id": 42,
                            "arxiv_id": "2603.99999v1",
                            "title": "Integration Test Paper",
                        },
                    }
                ],
            }
        }


def test_ingest_reindex_search_flow(client):
    fake_db = SimpleNamespace()
    app.dependency_overrides[get_db] = lambda: fake_db
    app.dependency_overrides[get_opensearch_client] = lambda: DummyOSClient()

    with patch("src.routers.papers.ingest_latest_cs_ai", return_value={"fetched": 2, "created": 2, "updated": 0}) as mock_ingest, patch(
        "src.routers.search.reindex_all_papers", return_value={"indexed": 2}
    ) as mock_reindex:
        try:
            ingest_resp = client.post("/api/v1/papers/ingest?max_results=2")
            reindex_resp = client.post("/api/v1/search/reindex")
            search_resp = client.post("/api/v1/search", json={"query": "integration", "size": 3})
        finally:
            app.dependency_overrides.clear()

    assert ingest_resp.status_code == 200
    assert ingest_resp.json() == {"fetched": 2, "created": 2, "updated": 0}

    assert reindex_resp.status_code == 200
    assert reindex_resp.json() == {"indexed": 2}

    assert search_resp.status_code == 200
    payload = search_resp.json()
    assert payload["total"] == 1
    assert payload["hits"][0]["paper_id"] == 42
    assert payload["hits"][0]["arxiv_id"] == "2603.99999v1"

    mock_ingest.assert_called_once_with(db=fake_db, max_results=2)
    mock_reindex.assert_called_once_with(fake_db)
