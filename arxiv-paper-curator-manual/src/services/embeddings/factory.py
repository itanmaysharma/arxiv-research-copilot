from functools import lru_cache

from src.services.embeddings.jina_client import JinaEmbeddingsClient


@lru_cache(maxsize=1)
def make_embeddings_client() -> JinaEmbeddingsClient:
    return JinaEmbeddingsClient()
