from functools import lru_cache

from src.config import settings
from src.services.ollama.client import OllamaClient


@lru_cache(maxsize=1)
def make_ollama_client() -> OllamaClient:
    return OllamaClient(
        base_url=settings.ollama.base_url,
        model=settings.ollama.model,
    )
