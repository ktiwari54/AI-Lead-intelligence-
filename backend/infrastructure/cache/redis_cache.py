from __future__ import annotations

import json
from typing import Any, Protocol

import redis.asyncio as aioredis


class CachePort(Protocol):
    async def get(self, key: str) -> Any | None: ...
    async def set(self, key: str, value: Any, ttl: int = 3600) -> None: ...
    async def delete(self, key: str) -> None: ...
    async def get_or_set(self, key: str, factory, ttl: int = 3600) -> Any: ...


class RedisCache:
    """Redis cache-aside adapter with namespaced keys."""

    def __init__(self, redis_url: str, env: str = "dev"):
        self._redis = aioredis.from_url(redis_url, decode_responses=True)
        self._env = env

    def _key(self, org_id: str, domain: str, key: str) -> str:
        return f"{self._env}:{org_id}:{domain}:{key}"

    async def get(self, key: str) -> Any | None:
        raw = await self._redis.get(key)
        if raw is None:
            return None
        return json.loads(raw)

    async def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        await self._redis.setex(key, ttl, json.dumps(value, default=str))

    async def delete(self, key: str) -> None:
        await self._redis.delete(key)

    async def get_or_set(self, key: str, factory, ttl: int = 3600) -> Any:
        cached = await self.get(key)
        if cached is not None:
            return cached
        lock_key = f"lock:{key}"
        acquired = await self._redis.set(lock_key, "1", nx=True, ex=30)
        if acquired:
            try:
                value = await factory()
                if value is not None:
                    await self.set(key, value, ttl)
                return value
            finally:
                await self._redis.delete(lock_key)
        return await factory()

    def namespaced(self, org_id: str, domain: str) -> NamespacedCache:
        return NamespacedCache(self, org_id, domain)


class NamespacedCache:
    def __init__(self, cache: RedisCache, org_id: str, domain: str):
        self._cache = cache
        self._org_id = org_id
        self._domain = domain

    def _key(self, key: str) -> str:
        return self._cache._key(self._org_id, self._domain, key)

    async def get(self, key: str) -> Any | None:
        return await self._cache.get(self._key(key))

    async def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        await self._cache.set(self._key(key), value, ttl)

    async def delete(self, key: str) -> None:
        await self._cache.delete(self._key(key))