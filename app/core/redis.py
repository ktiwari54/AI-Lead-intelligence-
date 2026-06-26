"""Redis client and cache utilities."""
import json
from typing import Any

import redis.asyncio as aioredis

from app.core.config import settings

_redis: aioredis.Redis | None = None


def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=5,
        )
    return _redis


async def check_redis_connection() -> bool:
    try:
        await get_redis().ping()
        return True
    except Exception:
        return False


class CacheService:
    """Thin wrapper around Redis for JSON caching."""

    def __init__(self, prefix: str = "", ttl: int = settings.REDIS_CACHE_TTL) -> None:
        self.prefix = prefix
        self.default_ttl = ttl
        self._redis = get_redis()

    def _key(self, key: str) -> str:
        return f"{self.prefix}:{key}" if self.prefix else key

    async def get(self, key: str) -> Any | None:
        raw = await self._redis.get(self._key(key))
        return json.loads(raw) if raw is not None else None

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        await self._redis.setex(
            self._key(key),
            ttl or self.default_ttl,
            json.dumps(value, default=str),
        )

    async def delete(self, key: str) -> None:
        await self._redis.delete(self._key(key))

    async def delete_pattern(self, pattern: str) -> None:
        keys = await self._redis.keys(self._key(pattern))
        if keys:
            await self._redis.delete(*keys)

    async def incr(self, key: str, ttl: int | None = None) -> int:
        val = await self._redis.incr(self._key(key))
        if val == 1 and ttl:
            await self._redis.expire(self._key(key), ttl)
        return val
