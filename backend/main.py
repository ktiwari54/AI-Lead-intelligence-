from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.middleware import RequestLoggingMiddleware, TenantMiddleware
from app.auth.router import router as auth_router
from app.users.router import router as users_router
from app.organizations.router import router as orgs_router
from app.companies.router import router as companies_router
from app.contacts.router import router as contacts_router
from app.search.router import router as search_router
from app.enrichment.router import router as enrichment_router
from app.ai.router import router as ai_router
from app.crm.router import router as crm_router
from app.billing.router import router as billing_router
from app.notifications.router import router as notifications_router
from app.admin.router import router as admin_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.core.database import engine
    from app.models import Base  # noqa: F401 – registers all models
    yield
    await engine.dispose()


app = FastAPI(
    title="AI Lead Intelligence Platform",
    version="1.0.0",
    description="Enterprise B2B lead discovery, enrichment, and AI scoring platform.",
    lifespan=lifespan,
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(TenantMiddleware)

V1 = "/api/v1"
app.include_router(auth_router, prefix=f"{V1}/auth", tags=["Auth"])
app.include_router(users_router, prefix=f"{V1}/users", tags=["Users"])
app.include_router(orgs_router, prefix=f"{V1}/organizations", tags=["Organizations"])
app.include_router(companies_router, prefix=f"{V1}/companies", tags=["Companies"])
app.include_router(contacts_router, prefix=f"{V1}/contacts", tags=["Contacts"])
app.include_router(search_router, prefix=f"{V1}/search", tags=["Search"])
app.include_router(enrichment_router, prefix=f"{V1}/enrichment", tags=["Enrichment"])
app.include_router(ai_router, prefix=f"{V1}/ai", tags=["AI"])
app.include_router(crm_router, prefix=f"{V1}/crm", tags=["CRM"])
app.include_router(billing_router, prefix=f"{V1}/billing", tags=["Billing"])
app.include_router(notifications_router, prefix=f"{V1}/notifications", tags=["Notifications"])
app.include_router(admin_router, prefix=f"{V1}/admin", tags=["Admin"])


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy", "version": "1.0.0"}
