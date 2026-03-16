from functools import lru_cache

from src.services.cache.redis_client import RedisCache


@lru_cache(maxsize=1)
def make_cache_client() -> RedisCache:
    return RedisCache()
