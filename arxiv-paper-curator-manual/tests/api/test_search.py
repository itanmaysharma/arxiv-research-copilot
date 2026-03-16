from types import SimpleNamespace
from unittest.mock import patch

from src.dependencies import get_db, get_opensearch_client
from src.main import app


class DummyOSClient:
    def search(self, index, body):
        if index == "papers_bm25":
            return {
                "hits": {
                    "total": {"value": 1},
                    "hits": [
                        {
                            "_score": 12.3,
                            "_source": {
                                "paper_id": 10,
                                "arxiv_id": "2603.06485v1",
                                "title": "PONTE",
                            },
                        }
                    ],
                }
            }
        raise AssertionError(f"Unexpected index: {index}")


def test_search_returns_hits(client):
    app.dependency_overrides[get_opensearch_client] = lambda: DummyOSClient()
    try:
        resp = client.post("/api/v1/search", json={"query": "ponte", "size": 3})
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["total"] == 1
    assert payload["hits"][0]["paper_id"] == 10
    assert payload["hits"][0]["arxiv_id"] == "2603.06485v1"


def test_reindex_endpoint_calls_service(client):
    fake_db = SimpleNamespace()
    app.dependency_overrides[get_db] = lambda: fake_db
    with patch("src.routers.search.reindex_all_papers", return_value={"indexed": 11}) as mock_reindex:
        try:
            resp = client.post("/api/v1/search/reindex")
        finally:
            app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert resp.json()["indexed"] == 11
    mock_reindex.assert_called_once_with(fake_db)
