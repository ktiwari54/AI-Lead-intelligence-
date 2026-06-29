from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from backend.app.common.cache import cache_get, cache_set


@dataclass
class RateLimitResult:
    allowed: bool
    limit: int
    remaining: int
    reset_seconds: int


async def check_rate_limit(
    key: str,
    *,
    limit: int = 60,
    window_seconds: int = 60,
) -> RateLimitResult:
    """Token-bucket rate limiter backed by Redis/cache."""
    cache_key = f"ratelimit:{key}"
    current = await cache_get(cache_key)
    count = int(current) if current else 0

    if count >= limit:
        return RateLimitResult(allowed=False, limit=limit, remaining=0, reset_seconds=window_seconds)

    await cache_set(cache_key, str(count + 1), ttl=window_seconds)
    return RateLimitResult(
        allowed=True,
        limit=limit,
        remaining=limit - count - 1,
        reset_seconds=window_seconds,
    )


def rate_limit_key(
    *,
    organization_id: UUID,
    user_id: UUID | None = None,
    api_key_id: UUID | None = None,
    endpoint: str | None = None,
) -> str:
    parts = [str(organization_id)]
    if api_key_id:
        parts.append(f"key:{api_key_id}")
    elif user_id:
        parts.append(f"user:{user_id}")
    if endpoint:
        parts.append(endpoint)
    return ":".join(parts)