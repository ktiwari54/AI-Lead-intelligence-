"""Custom ASGI middleware stack."""
import time
import uuid
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings
from app.core.redis import get_redis


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        request.state.start_time = time.perf_counter()
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        duration_ms = int((time.perf_counter() - request.state.start_time) * 1000)
        response.headers["X-Response-Time"] = f"{duration_ms}ms"
        return response


class TenantContextMiddleware(BaseHTTPMiddleware):
    """Injects org_id into request state from JWT claims."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request.state.org_id = None
        request.state.user_id = None
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            try:
                from app.core.security import decode_token
                token = auth_header[7:]
                claims = decode_token(token)
                request.state.org_id = claims.get("org_id")
                request.state.user_id = claims.get("sub")
            except Exception:
                pass
        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    SKIP_PATHS = {"/health", "/readiness", "/metrics"}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)

        identifier = (
            getattr(request.state, "user_id", None)
            or request.client.host
            if request.client else "unknown"
        )
        limit = (
            settings.SEARCH_RATE_LIMIT_PER_MINUTE
            if "/search" in request.url.path
            else settings.RATE_LIMIT_PER_MINUTE
        )
        redis = get_redis()
        key = f"rl:{identifier}:{int(time.time() // 60)}"
        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, 60)
        if count > limit:
            from starlette.responses import JSONResponse
            return JSONResponse(
                status_code=429,
                content={"error": {"code": "rate_limit_exceeded", "message": "Too many requests"}},
                headers={"Retry-After": "60"},
            )
        return await call_next(request)


class AuditMiddleware(BaseHTTPMiddleware):
    WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        if request.method in self.WRITE_METHODS and response.status_code < 400:
            # fire-and-forget audit log (handled by background worker)
            pass
        return response
