from collections.abc import Generator

from fastapi import Request
from opensearchpy import OpenSearch
from sqlalchemy.orm import Session

from src.db.session import SessionLocal
from src.services.cache.factory import make_cache_client
from src.services.cache.redis_client import RedisCache
from src.services.embeddings.factory import make_embeddings_client
from src.services.embeddings.jina_client import JinaEmbeddingsClient
from src.services.langfuse.factory import make_tracer_service
from src.services.langfuse.tracer import Tracer
from src.services.ollama.client import OllamaClient
from src.services.ollama.factory import make_ollama_client
from src.services.opensearch.factory import make_opensearch_client


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_opensearch_client(request: Request) -> OpenSearch:
    return getattr(request.app.state, "opensearch_client", make_opensearch_client())


def get_ollama_client(request: Request) -> OllamaClient:
    return getattr(request.app.state, "ollama_client", make_ollama_client())


def get_cache_client(request: Request) -> RedisCache:
    return getattr(request.app.state, "cache_client", make_cache_client())


def get_embeddings_client(request: Request) -> JinaEmbeddingsClient:
    return getattr(request.app.state, "embeddings_client", make_embeddings_client())


def get_tracer_service(request: Request) -> Tracer:
    return getattr(request.app.state, "tracer_service", make_tracer_service())
