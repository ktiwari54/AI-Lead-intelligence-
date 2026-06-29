from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import PlainTextResponse

from backend.config import settings

# Register reference ORM models (Industry, Country, etc.) for mapper resolution
import backend.app.common.reference  # noqa: F401
# Register discovery connectors (apollo, mock_discovery, etc.)
import backend.connectors  # noqa: F401
from backend.app.auth.router import router as auth_router
from backend.app.users.router import router as users_router
from backend.app.organizations.router import router as orgs_router
from backend.app.companies.router import router as companies_router
from backend.app.contacts.router import router as contacts_router
from backend.app.search.router import router as search_router
from backend.app.ai.router import router as ai_router
from backend.app.crm.router import router as crm_router
from backend.app.enrichment.router import router as enrichment_router
from backend.app.billing.router import router as billing_router
from backend.app.notifications.router import router as notifications_router
from backend.app.exports.router import router as exports_router
from backend.app.integrations.router import router as integrations_router
from backend.app.admin.router import router as admin_router
from backend.app.analytics.router import router as analytics_router
from backend.app.discovery.router import router as discovery_router
from backend.app.workflows.router import router as workflows_router
from backend.app.platform.router import router as platform_router
from backend.infrastructure.observability.metrics import metrics


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize connections, warm caches, etc.
    yield
    # Shutdown: close connections gracefully


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Enterprise AI Lead Intelligence Platform API",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

API_V1 = "/api/v1"

app.include_router(auth_router,          prefix=f"{API_V1}/auth",          tags=["Authentication"])
app.include_router(users_router,         prefix=f"{API_V1}/users",         tags=["Users"])
app.include_router(orgs_router,          prefix=f"{API_V1}/organizations",  tags=["Organizations"])
app.include_router(companies_router,     prefix=f"{API_V1}/companies",      tags=["Companies"])
app.include_router(contacts_router,      prefix=f"{API_V1}/contacts",       tags=["Contacts"])
app.include_router(search_router,        prefix=f"{API_V1}/search",         tags=["Search"])
app.include_router(ai_router,            prefix=f"{API_V1}/ai",             tags=["AI"])
app.include_router(crm_router,           prefix=f"{API_V1}/crm",            tags=["CRM"])
app.include_router(enrichment_router,    prefix=f"{API_V1}/enrichment",     tags=["Enrichment"])
app.include_router(billing_router,       prefix=f"{API_V1}/billing",        tags=["Billing"])
app.include_router(notifications_router, prefix=f"{API_V1}/notifications",  tags=["Notifications"])
app.include_router(exports_router,       prefix=f"{API_V1}/exports",        tags=["Exports"])
app.include_router(integrations_router,  prefix=f"{API_V1}/integrations",   tags=["Integrations"])
app.include_router(admin_router,         prefix=f"{API_V1}/admin",          tags=["Admin"])
app.include_router(analytics_router,     prefix=f"{API_V1}/analytics",      tags=["Analytics"])
app.include_router(discovery_router,     prefix=f"{API_V1}",                tags=["Discovery"])
app.include_router(workflows_router,     prefix=f"{API_V1}",                tags=["Workflows"])
app.include_router(platform_router,      prefix=f"{API_V1}",                tags=["Platform"])


@app.get("/health", tags=["Health"])
async def health_check():
    metrics.counter("http_requests_total", {"endpoint": "health", "status": "200"}).inc()
    return {"status": "healthy", "version": settings.APP_VERSION, "environment": settings.ENVIRONMENT}


@app.get("/metrics", tags=["Observability"], include_in_schema=False)
async def prometheus_metrics():
    """Prometheus scrape endpoint (free observability stack)."""
    return PlainTextResponse(
        content=metrics.export_prometheus(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )
