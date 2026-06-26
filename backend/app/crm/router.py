import uuid
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.database import get_db
from backend.app.crm.models import CRMPipeline, CRMPipelineStage, CRMDeal, CRMTask, Tag, Note, Activity, LeadList
from backend.app.common.response import APIResponse, PaginatedResponse
from backend.app.common.pagination import pagination_params, PaginationParams
from backend.app.common.deps import get_current_user_id, get_current_org_id
from backend.app.common.exceptions import NotFoundError

router = APIRouter()


# ─── Pipelines ────────────────────────────────────────────────────────────────

class PipelineCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    is_default: bool = False


@router.get("/pipelines", response_model=APIResponse)
async def list_pipelines(
    org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CRMPipeline).where(
            CRMPipeline.organization_id == org_id, CRMPipeline.deleted_at.is_(None)
        )
    )
    return APIResponse(data=[p.to_dict() for p in result.scalars().all()])


@router.post("/pipelines", response_model=APIResponse, status_code=201)
async def create_pipeline(
    data: PipelineCreate,
    org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    pipeline = CRMPipeline(organization_id=org_id, **data.model_dump())
    db.add(pipeline)
    await db.flush()
    return APIResponse(data=pipeline.to_dict(), message="Pipeline created")


# ─── Deals ───────────────────────────────────────────────────────────────────────────

class DealCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    pipeline_id: uuid.UUID
    stage_id: uuid.UUID
    contact_id: uuid.UUID | None = None
    company_id: uuid.UUID | None = None
    value: float | None = None
    currency: str = "USD"
    close_date: str | None = None


@router.get("/deals", response_model=PaginatedResponse)
async def list_deals(
    pipeline_id: uuid.UUID | None = Query(None),
    pagination: PaginationParams = Depends(pagination_params),
    org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(CRMDeal).where(
        CRMDeal.organization_id == org_id, CRMDeal.deleted_at.is_(None)
    )
    if pipeline_id:
        stmt = stmt.where(CRMDeal.pipeline_id == pipeline_id)
    count = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total = count.scalar()
    result = await db.execute(stmt.offset(pagination.offset).limit(pagination.per_page))
    deals = [d.to_dict() for d in result.scalars().all()]
    return PaginatedResponse.create(data=deals, total=total, page=pagination.page, per_page=pagination.per_page)


@router.post("/deals", response_model=APIResponse, status_code=201)
async def create_deal(
    data: DealCreate,
    org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    deal = CRMDeal(organization_id=org_id, **data.model_dump(exclude_none=True))
    db.add(deal)
    await db.flush()
    return APIResponse(data=deal.to_dict(), message="Deal created")


# ─── Tasks ───────────────────────────────────────────────────────────────────────────

class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    task_type: str = "task"
    priority: str = "medium"
    due_at: str | None = None
    contact_id: uuid.UUID | None = None
    company_id: uuid.UUID | None = None
    description: str | None = None


@router.get("/tasks", response_model=PaginatedResponse)
async def list_tasks(
    pagination: PaginationParams = Depends(pagination_params),
    org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(CRMTask).where(
        CRMTask.organization_id == org_id, CRMTask.deleted_at.is_(None)
    )
    count = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total = count.scalar()
    result = await db.execute(stmt.offset(pagination.offset).limit(pagination.per_page))
    tasks = [t.to_dict() for t in result.scalars().all()]
    return PaginatedResponse.create(data=tasks, total=total, page=pagination.page, per_page=pagination.per_page)


@router.post("/tasks", response_model=APIResponse, status_code=201)
async def create_task(
    data: TaskCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    task = CRMTask(organization_id=org_id, created_by=user_id, **data.model_dump(exclude_none=True))
    db.add(task)
    await db.flush()
    return APIResponse(data=task.to_dict(), message="Task created")


# ─── Tags ───────────────────────────────────────────────────────────────────────────

class TagCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    color: str | None = None


@router.get("/tags", response_model=APIResponse)
async def list_tags(
    org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Tag).where(Tag.organization_id == org_id, Tag.deleted_at.is_(None))
    )
    return APIResponse(data=[t.to_dict() for t in result.scalars().all()])


@router.post("/tags", response_model=APIResponse, status_code=201)
async def create_tag(
    data: TagCreate,
    org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    tag = Tag(organization_id=org_id, **data.model_dump(exclude_none=True))
    db.add(tag)
    await db.flush()
    return APIResponse(data=tag.to_dict(), message="Tag created")


# ─── Lists ───────────────────────────────────────────────────────────────────────────

class ListCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    list_type: str = "static"


@router.get("/lists", response_model=APIResponse)
async def list_lead_lists(
    org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(LeadList).where(LeadList.organization_id == org_id, LeadList.deleted_at.is_(None))
    )
    return APIResponse(data=[l.to_dict() for l in result.scalars().all()])


@router.post("/lists", response_model=APIResponse, status_code=201)
async def create_list(
    data: ListCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    lead_list = LeadList(organization_id=org_id, created_by=user_id, **data.model_dump(exclude_none=True))
    db.add(lead_list)
    await db.flush()
    return APIResponse(data=lead_list.to_dict(), message="List created")
