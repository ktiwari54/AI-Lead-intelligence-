import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.database import get_db
from backend.app.common.response import APIResponse
from backend.app.common.deps import get_current_org_id

router = APIRouter()


@router.get("/overview", response_model=APIResponse)
async def get_overview(
    org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    from backend.app.companies.models import Company
    from backend.app.contacts.models import Contact
    from backend.app.searches.models import Search
    from backend.app.exports.models import Export

    companies_count = await db.execute(
        select(func.count(Company.id)).where(
            Company.organization_id == org_id, Company.deleted_at.is_(None)
        )
    )
    contacts_count = await db.execute(
        select(func.count(Contact.id)).where(
            Contact.organization_id == org_id, Contact.deleted_at.is_(None)
        )
    )

    return APIResponse(data={
        "companies": companies_count.scalar(),
        "contacts": contacts_count.scalar(),
    })
