"""Application entry point."""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import ORJSONResponse

from app.core.config import settings
from app.core.database import engine, Base
from app.core.logging import configure_logging
from app.core.middleware import (
    RequestIDMiddleware,
    RateLimitMiddleware,
    TenantContextMiddleware,
    AuditMiddleware,
)
from app.core.metrics import setup_metrics
from app.core.tracing import setup_tracing
from app.core.exceptions import register_exception_handlers

# Routers
from app.auth.router import router as auth_router
from app.organizations.router import router as orgs_router
from app.users.router import router as users_router
from app.companies.router import router as companies_router
from app.contacts.router import router as contacts_router
from app.search.router import router as search_router
from app.ai.router import router as ai_router
from app.connectors.router import router as connectors_router
from app.crm.router import router as crm_router
from app.exports.router import router as exports_router
from app.analytics.router import router as analytics_router
from app.notifications.router import router as notifications_router
from app.billing.router import router as billing_router
from app.workflows.router import router as workflows_router
from app.admin.router import router as admin_router
from app.enrichment.router import router as enrichment_router


configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup and shutdown lifecycle."""
    setup_tracing(app)
    setup_metrics(app)
    yield
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version="3.0.0",
        description="Enterprise AI Lead Intelligence Platform API",
        docs_url="/api/docs" if settings.DEBUG else None,
        redoc_url="/api/redoc" if settings.DEBUG else None,
        openapi_url="/api/openapi.json",
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
    )

    # Middleware (order matters: outermost runs first on request)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(AuditMiddleware)
    app.add_middleware(TenantContextMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(GZipMiddleware, minimum_size=1024)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Correlation-ID"],
    )

    register_exception_handlers(app)

    # API v1
    prefix = "/api/v1"
    app.include_router(auth_router,          prefix=f"{prefix}/auth",          tags=["Auth"])
    app.include_router(orgs_router,          prefix=f"{prefix}/organizations",  tags=["Organizations"])
    app.include_router(users_router,         prefix=f"{prefix}/users",          tags=["Users"])
    app.include_router(companies_router,     prefix=f"{prefix}/companies",      tags=["Companies"])
    app.include_router(contacts_router,      prefix=f"{prefix}/contacts",       tags=["Contacts"])
    app.include_router(search_router,        prefix=f"{prefix}/search",         tags=["Search"])
    app.include_router(ai_router,            prefix=f"{prefix}/ai",             tags=["AI"])
    app.include_router(connectors_router,    prefix=f"{prefix}/connectors",     tags=["Connectors"])
    app.include_router(crm_router,           prefix=f"{prefix}/crm",            tags=["CRM"])
    app.include_router(exports_router,       prefix=f"{prefix}/exports",        tags=["Exports"])
    app.include_router(analytics_router,     prefix=f"{prefix}/analytics",      tags=["Analytics"])
    app.include_router(notifications_router, prefix=f"{prefix}/notifications",  tags=["Notifications"])
    app.include_router(billing_router,       prefix=f"{prefix}/billing",        tags=["Billing"])
    app.include_router(workflows_router,     prefix=f"{prefix}/workflows",      tags=["Workflows"])
    app.include_router(admin_router,         prefix=f"{prefix}/admin",          tags=["Admin"])
    app.include_router(enrichment_router,    prefix=f"{prefix}/enrichment",     tags=["Enrichment"])

    @app.get("/health", tags=["Health"])
    async def health() -> dict:
        return {"status": "ok", "version": "3.0.0"}

    @app.get("/readiness", tags=["Health"])
    async def readiness(request: Request) -> dict:
        from app.core.database import check_db_connection
        from app.core.redis import check_redis_connection
        db_ok = await check_db_connection()
        redis_ok = await check_redis_connection()
        if not (db_ok and redis_ok):
            return ORJSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"status": "degraded", "db": db_ok, "redis": redis_ok},
            )
        return {"status": "ready", "db": db_ok, "redis": redis_ok}

    return app


app = create_app()
