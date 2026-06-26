"""Request tracing middleware - adds X-Request-ID to every request/response."""
from __future__ import annotations
import time
import uuid
import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = structlog.get_logger()


class RequestTracingMiddleware(BaseHTTPMiddleware):
    """Adds X-Request-ID header and structured request logging."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        start_time = time.perf_counter()

        # Bind to structlog context
        with structlog.contextvars.bound_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        ):
            logger.info("request_started")

            try:
                response = await call_next(request)
            except Exception as exc:
                logger.exception("request_failed", error=str(exc))
                raise

            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.info(
                "request_completed",
                status_code=response.status_code,
                duration_ms=duration_ms,
            )

            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{duration_ms}ms"
            return response
