import uuid
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database import get_db
from backend.app.integrations.models import ConnectorConfig, ConnectorJob
from backend.app.common.response import APIResponse, PaginatedResponse
from backend.app.common.pagination import pagination_params, PaginationParams
from backend.app.common.deps import get_current_org_id

router = APIRouter()


class ConnectorConfigCreate(BaseModel):
    connector_type: str
    name: str
    credentials: dict
    settings: dict = {}


@router.get("/connectors", response_model=APIResponse)
async def list_connectors(
    org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    from backend.connectors.registry import ConnectorRegistry
    connectors = ConnectorRegistry.list_available()
    return APIResponse(data=connectors)


@router.get("/configs", response_model=APIResponse)
async def list_configs(
    org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ConnectorConfig).where(
            ConnectorConfig.organization_id == org_id, ConnectorConfig.deleted_at.is_(None)
        )
    )
    configs = [c.to_dict() for c in result.scalars().all()]
    return APIResponse(data=configs)


@router.post("/configs", response_model=APIResponse, status_code=201)
async def create_config(
    data: ConnectorConfigCreate,
    org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    config = ConnectorConfig(
        organization_id=org_id,
        connector_type=data.connector_type,
        name=data.name,
        credentials=data.credentials,
        settings=data.settings,
    )
    db.add(config)
    await db.flush()
    return APIResponse(data=config.to_dict(), message="Connector configured")


@router.get("/jobs", response_model=PaginatedResponse)
async def list_jobs(
    pagination: PaginationParams = Depends(pagination_params),
    org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import func
    stmt = select(ConnectorJob).where(
        ConnectorJob.organization_id == org_id
    ).order_by(ConnectorJob.created_at.desc())
    count = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total = count.scalar()
    result = await db.execute(stmt.offset(pagination.offset).limit(pagination.per_page))
    jobs = [j.to_dict() for j in result.scalars().all()]
    return PaginatedResponse.create(data=jobs, total=total, page=pagination.page, per_page=pagination.per_page)
