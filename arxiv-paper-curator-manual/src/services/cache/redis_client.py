import json
from typing import Any

import redis

from src.config import settings


class RedisCache:
    def __init__(self, redis_url: str | None = None) -> None:
        self.client = redis.Redis.from_url(redis_url or settings.redis.url, decode_responses=True)

    def get_json(self, key: str) -> dict[str, Any] | None:
        value = self.client.get(key)
        if not value:
            return None
        return json.loads(value)

    def set_json(self, key: str, value: dict[str, Any], ttl_seconds: int = 3600) -> None:
        self.client.setex(key, ttl_seconds, json.dumps(value))

    def ping(self) -> bool:
        return bool(self.client.ping())
