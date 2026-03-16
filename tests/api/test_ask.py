from unittest.mock import patch

from src.dependencies import get_cache_client, get_ollama_client, get_opensearch_client
from src.main import app


def test_ask_returns_answer_and_headers(client):
    mock_cache = type("Cache", (), {})()
    mock_cache.get_json = lambda _k: None
    mock_cache.set_json = lambda *_args, **_kwargs: None

    mock_ollama = type("Ollama", (), {})()
    mock_ollama.generate = lambda _p: "Grounded answer."

    app.dependency_overrides[get_cache_client] = lambda: mock_cache
    app.dependency_overrides[get_ollama_client] = lambda: mock_ollama
    app.dependency_overrides[get_opensearch_client] = lambda: object()
    with patch(
        "src.routers.ask.build_context",
        return_value=("ctx", [{"arxiv_id": "2603.06485v1", "chunk_index": 1}]),
    ):
        try:
            resp = client.post(
                "/api/v1/ask",
                json={"question": "What does PONTE optimize for?", "top_k": 3},
            )
        finally:
            app.dependency_overrides.clear()

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["answer"] == "Grounded answer."
    assert len(payload["sources"]) == 1
    assert payload["search_mode"] == "chunk_bm25"
    assert payload["retrieval_attempts"] == 1
    assert payload["confidence"] > 0
    assert payload["citations"] == ["2603.06485v1"]
    assert resp.headers["x-cache"] == "MISS"
    assert "x-trace-id" in resp.headers
    assert "x-latency-ms" in resp.headers


def test_ask_cache_hit_skips_generation(client):
    mock_cache = type("Cache", (), {})()
    mock_cache.get_json = lambda _k: {
        "answer": "Cached answer.",
        "sources": [{"arxiv_id": "2603.06485v1", "chunk_index": 2}],
    }
    mock_cache.set_json = lambda *_args, **_kwargs: None

    mock_ollama = type("Ollama", (), {})()
    mock_ollama.generate = lambda _p: (_ for _ in ()).throw(AssertionError("should not generate"))

    app.dependency_overrides[get_cache_client] = lambda: mock_cache
    app.dependency_overrides[get_ollama_client] = lambda: mock_ollama
    app.dependency_overrides[get_opensearch_client] = lambda: object()
    with patch(
        "src.routers.ask.build_context",
        side_effect=AssertionError("build_context should not be called on cache hit"),
    ):
        try:
            resp = client.post(
                "/api/v1/ask",
                json={"question": "What does PONTE optimize for?", "top_k": 3},
            )
        finally:
            app.dependency_overrides.clear()

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["answer"] == "Cached answer."
    assert payload["search_mode"] == "chunk_bm25"
    assert payload["retrieval_attempts"] == 1
    assert payload["citations"] == ["2603.06485v1"]
    assert resp.headers["x-cache"] == "HIT"
