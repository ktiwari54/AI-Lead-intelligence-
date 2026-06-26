import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.app.organizations.schemas import OrganizationUpdate, OrganizationResponse
from backend.app.organizations.service import OrganizationService
from backend.app.common.response import APIResponse
from backend.app.common.deps import get_current_org_id

router = APIRouter()


@router.get("/current", response_model=APIResponse[OrganizationResponse])
async def get_current_org(
    org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    org = await OrganizationService(db).get_by_id(org_id)
    return APIResponse(data=OrganizationResponse.model_validate(org))


@router.patch("/current", response_model=APIResponse[OrganizationResponse])
async def update_org(
    data: OrganizationUpdate,
    org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    org = await OrganizationService(db).update(org_id, data)
    return APIResponse(data=OrganizationResponse.model_validate(org))
