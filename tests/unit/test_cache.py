from unittest.mock import MagicMock, patch

from src.services.cache.redis_client import RedisCache


def test_get_json_returns_none_when_missing():
    with patch("src.services.cache.redis_client.redis.Redis.from_url") as mock_from_url:
        client = MagicMock()
        client.get.return_value = None
        mock_from_url.return_value = client

        cache = RedisCache(redis_url="redis://test:6379/0")
        result = cache.get_json("missing")

    assert result is None


def test_set_and_get_json_roundtrip():
    with patch("src.services.cache.redis_client.redis.Redis.from_url") as mock_from_url:
        client = MagicMock()
        client.get.return_value = '{"answer":"ok","sources":[{"x":1}]}'
        mock_from_url.return_value = client

        cache = RedisCache(redis_url="redis://test:6379/0")
        cache.set_json("k1", {"answer": "ok", "sources": [{"x": 1}]}, ttl_seconds=120)
        result = cache.get_json("k1")

    client.setex.assert_called_once()
    assert result == {"answer": "ok", "sources": [{"x": 1}]}


def test_ping_returns_true():
    with patch("src.services.cache.redis_client.redis.Redis.from_url") as mock_from_url:
        client = MagicMock()
        client.ping.return_value = True
        mock_from_url.return_value = client

        cache = RedisCache(redis_url="redis://test:6379/0")
        assert cache.ping() is True
