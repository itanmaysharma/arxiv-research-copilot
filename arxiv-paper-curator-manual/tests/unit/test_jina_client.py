from src.services.embeddings.jina_client import JinaEmbeddingsClient


def test_embed_query_without_api_key_returns_vector() -> None:
    client = JinaEmbeddingsClient(api_key="", dimensions=16)
    vector = client.embed_query("test query")

    assert len(vector) == 16
    assert all(isinstance(v, float) for v in vector)


def test_embed_passages_without_api_key_is_deterministic() -> None:
    client = JinaEmbeddingsClient(api_key="", dimensions=8)
    texts = ["alpha", "beta"]

    first = client.embed_passages(texts)
    second = client.embed_passages(texts)

    assert first == second
    assert len(first) == 2
    assert len(first[0]) == 8
