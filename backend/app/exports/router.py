import uuid
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.database import get_db
from backend.app.exports.models import Export
from backend.app.common.response import APIResponse, PaginatedResponse
from backend.app.common.pagination import pagination_params, PaginationParams
from backend.app.common.deps import get_current_user_id, get_current_org_id

router = APIRouter()


class ExportRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    format: str = "csv"
    filters: dict = Field(default_factory=dict)
    export_type: str = "contacts"


@router.post("/", response_model=APIResponse, status_code=202)
async def create_export(
    request: ExportRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    export = Export(
        organization_id=org_id,
        created_by=user_id,
        name=request.name,
        format=request.format,
        filters=request.filters,
        status="pending",
    )
    db.add(export)
    await db.flush()

    from backend.workers.tasks.export import generate_export_task
    generate_export_task.delay(str(export.id), request.export_type)

    return APIResponse(data={"id": str(export.id)}, message="Export queued")


@router.get("/", response_model=PaginatedResponse)
async def list_exports(
    pagination: PaginationParams = Depends(pagination_params),
    org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Export).where(
        Export.organization_id == org_id, Export.deleted_at.is_(None)
    ).order_by(Export.created_at.desc())
    count = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total = count.scalar()
    result = await db.execute(stmt.offset(pagination.offset).limit(pagination.per_page))
    exports = [e.to_dict() for e in result.scalars().all()]
    return PaginatedResponse.create(data=exports, total=total, page=pagination.page, per_page=pagination.per_page)


@router.get("/{export_id}", response_model=APIResponse)
async def get_export(
    export_id: uuid.UUID,
    org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Export).where(Export.id == export_id, Export.organization_id == org_id)
    )
    export = result.scalar_one_or_none()
    if not export:
        from backend.app.common.exceptions import NotFoundError
        raise NotFoundError("Export not found")
    return APIResponse(data=export.to_dict())
