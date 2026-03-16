import hashlib
from collections.abc import Iterable

import httpx

from src.config import settings


class JinaEmbeddingsClient:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        dimensions: int | None = None,
    ) -> None:
        self.api_key = (api_key if api_key is not None else settings.embeddings.api_key).strip()
        self.base_url = (base_url or settings.embeddings.base_url).rstrip("/")
        self.model = model or settings.embeddings.model
        self.dimensions = dimensions or settings.embeddings.dimensions

    def embed_passages(self, texts: list[str], batch_size: int = 64) -> list[list[float]]:
        return self._embed_texts(texts=texts, task="retrieval.passage", batch_size=batch_size)

    def embed_query(self, query: str) -> list[float]:
        vectors = self._embed_texts(texts=[query], task="retrieval.query", batch_size=1)
        return vectors[0]

    def _embed_texts(self, texts: list[str], task: str, batch_size: int) -> list[list[float]]:
        if not texts:
            return []

        if not self.api_key:
            return [self._dummy_embedding(t) for t in texts]

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        embeddings: list[list[float]] = []
        with httpx.Client(timeout=30.0) as client:
            for batch in self._chunks(texts, batch_size):
                payload = {
                    "model": self.model,
                    "task": task,
                    "dimensions": self.dimensions,
                    "input": batch,
                }
                response = client.post(self.base_url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json().get("data", [])
                embeddings.extend(item["embedding"] for item in data)

        return embeddings

    def _dummy_embedding(self, text: str) -> list[float]:
        # Deterministic fallback so local dev can run without paid API access.
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        vector = [0.0] * self.dimensions
        for i in range(self.dimensions):
            byte = digest[i % len(digest)]
            vector[i] = (byte / 255.0) * 2.0 - 1.0
        return vector

    @staticmethod
    def _chunks(items: list[str], batch_size: int) -> Iterable[list[str]]:
        for i in range(0, len(items), batch_size):
            yield items[i : i + batch_size]
