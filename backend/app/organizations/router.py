from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.common.dependencies import get_current_org
from app.organizations import service
from app.organizations.schemas import OrganizationOut, OrganizationUpdate

router = APIRouter()


@router.get("/me", response_model=OrganizationOut)
async def get_my_org(org=Depends(get_current_org)):
    return org


@router.patch("/me", response_model=OrganizationOut)
async def update_my_org(
    data: OrganizationUpdate,
    db: AsyncSession = Depends(get_db),
    org=Depends(get_current_org),
):
    return await service.update_organization(org, data)
