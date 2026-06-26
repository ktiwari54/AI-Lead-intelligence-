"""Redis sliding-window rate limiter middleware."""
from __future__ import annotations
import time
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

import redis.asyncio as aioredis
from backend.config import get_settings

_redis_client = None


async def get_redis():
    global _redis_client
    if _redis_client is None:
        settings = get_settings()
        _redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_client


# Route-specific limits: (requests, window_seconds)
RATE_LIMITS: dict[str, tuple[int, int]] = {
    "/api/v1/auth/login": (10, 60),
    "/api/v1/auth/register": (5, 60),
    "/api/v1/search": (30, 60),
    "/api/v1/ai/score": (20, 60),
    "/api/v1/enrichment": (50, 60),
    "default": (120, 60),
}


def _get_limit(path: str) -> tuple[int, int]:
    for prefix, limit in RATE_LIMITS.items():
        if prefix != "default" and path.startswith(prefix):
            return limit
    return RATE_LIMITS["default"]


def _client_identifier(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    ip = forwarded.split(",")[0].strip() if forwarded else request.client.host if request.client else "unknown"
    # Include user identifier if JWT is present
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        import hashlib
        token_hash = hashlib.sha256(auth[7:].encode()).hexdigest()[:16]
        return f"user:{token_hash}"
    return f"ip:{ip}"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding window rate limit middleware using Redis sorted sets."""

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip health checks and docs
        if request.url.path in ("/health", "/api/docs", "/api/openapi.json", "/api/redoc"):
            return await call_next(request)

        limit, window = _get_limit(request.url.path)
        client_id = _client_identifier(request)
        key = f"rate_limit:{client_id}:{request.url.path}"
        now = time.time()
        window_start = now - window

        try:
            redis = await get_redis()
            pipe = redis.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zcard(key)
            pipe.zadd(key, {str(now): now})
            pipe.expire(key, window)
            results = await pipe.execute()
            request_count = results[1]

            if request_count >= limit:
                retry_after = int(window - (now - window_start))
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Try again in {retry_after}s.",
                    headers={"Retry-After": str(retry_after), "X-RateLimit-Limit": str(limit), "X-RateLimit-Window": str(window)},
                )

            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = str(max(0, limit - request_count - 1))
            response.headers["X-RateLimit-Window"] = str(window)
            return response

        except HTTPException:
            raise
        except Exception:
            # If Redis is down, fail open
            return await call_next(request)
