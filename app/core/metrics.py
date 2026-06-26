"""Prometheus metrics setup."""
from fastapi import FastAPI
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.requests import Request
from starlette.responses import Response

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "path", "status"]
)
HTTP_REQUEST_DURATION = Histogram(
    "http_request_duration_seconds", "HTTP request duration", ["method", "path"]
)
SEARCH_REQUESTS_TOTAL = Counter(
    "search_requests_total", "Total search requests", ["org_id", "search_type"]
)
CREDIT_DEDUCTIONS_TOTAL = Counter(
    "credit_deductions_total", "Total credit deductions", ["org_id", "action"]
)
AI_SCORING_DURATION = Histogram(
    "ai_scoring_duration_seconds", "AI scoring latency"
)


def setup_metrics(app: FastAPI) -> None:
    @app.get("/metrics", include_in_schema=False)
    async def metrics() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
