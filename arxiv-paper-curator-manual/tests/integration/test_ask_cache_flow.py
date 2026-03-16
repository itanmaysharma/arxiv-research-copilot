from unittest.mock import patch

from src.dependencies import get_cache_client, get_ollama_client, get_opensearch_client
from src.main import app


def test_ask_cache_miss_then_hit(client):
    class Cache:
        def __init__(self):
            self._calls = 0
            self.set_count = 0

        def get_json(self, _key):
            self._calls += 1
            if self._calls == 1:
                return None
            return {"answer": "cached-answer", "sources": [{"arxiv_id": "2603.06485v1", "chunk_index": 1}]}

        def set_json(self, *_args, **_kwargs):
            self.set_count += 1

    class Ollama:
        def __init__(self):
            self.calls = 0

        def generate(self, _prompt):
            self.calls += 1
            return "generated-answer"

    cache = Cache()
    ollama = Ollama()

    app.dependency_overrides[get_cache_client] = lambda: cache
    app.dependency_overrides[get_ollama_client] = lambda: ollama
    app.dependency_overrides[get_opensearch_client] = lambda: object()
    with patch(
        "src.routers.ask.build_context",
        return_value=("ctx", [{"arxiv_id": "2603.06485v1", "chunk_index": 1}]),
    ):
        try:
            first = client.post(
                "/api/v1/ask",
                json={"question": "What does PONTE optimize for?", "top_k": 3},
            )
            second = client.post(
                "/api/v1/ask",
                json={"question": "What does PONTE optimize for?", "top_k": 3},
            )
        finally:
            app.dependency_overrides.clear()

    assert first.status_code == 200
    assert first.json()["answer"] == "generated-answer"
    assert first.headers["x-cache"] == "MISS"

    assert second.status_code == 200
    assert second.json()["answer"] == "cached-answer"
    assert second.headers["x-cache"] == "HIT"

    assert ollama.calls == 1
    assert cache.set_count == 1
