import json
from typing import Any
import redis.asyncio as aioredis
from backend.config import settings

_redis: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis


async def cache_get(key: str) -> Any | None:
    r = await get_redis()
    value = await r.get(key)
    return json.loads(value) if value else None


async def cache_set(key: str, value: Any, ttl: int = settings.CACHE_TTL) -> None:
    r = await get_redis()
    await r.setex(key, ttl, json.dumps(value, default=str))


async def cache_delete(key: str) -> None:
    r = await get_redis()
    await r.delete(key)


async def cache_delete_pattern(pattern: str) -> None:
    r = await get_redis()
    keys = await r.keys(pattern)
    if keys:
        await r.delete(*keys)


# Cache key builders
def company_cache_key(org_id: str, company_id: str) -> str:
    return f"company:{org_id}:{company_id}"


def contact_cache_key(org_id: str, contact_id: str) -> str:
    return f"contact:{org_id}:{contact_id}"


def permissions_cache_key(user_id: str) -> str:
    return f"permissions:{user_id}"


def industry_list_cache_key() -> str:
    return "reference:industries"


def country_list_cache_key() -> str:
    return "reference:countries"


def technology_list_cache_key() -> str:
    return "reference:technologies"
