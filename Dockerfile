FROM python:3.13-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

# ---- API image ----
FROM base AS api
COPY . .
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# ---- Worker image ----
FROM base AS worker
COPY . .
CMD ["celery", "-A", "workers.celery_app", "worker", "--loglevel=info", "--concurrency=8"]

# ---- Beat image ----
FROM base AS beat
COPY . .
CMD ["celery", "-A", "workers.celery_app", "beat", "--loglevel=info", "--scheduler", "celery.beat:PersistentScheduler"]
