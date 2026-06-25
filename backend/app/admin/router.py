from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.common.dependencies import get_current_user
from app.models.identity import Organization, User
from app.models.companies import Company
from app.models.contacts import Contact
from app.models.search import Search

router = APIRouter()


@router.get("/stats")
async def platform_stats(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    orgs = (await db.execute(select(func.count()).select_from(Organization).where(Organization.is_deleted == False))).scalar()
    users = (await db.execute(select(func.count()).select_from(User).where(User.is_deleted == False))).scalar()
    companies = (await db.execute(select(func.count()).select_from(Company).where(Company.is_deleted == False))).scalar()
    contacts = (await db.execute(select(func.count()).select_from(Contact).where(Contact.is_deleted == False))).scalar()
    searches = (await db.execute(select(func.count()).select_from(Search))).scalar()
    return {"organizations": orgs, "users": users, "companies": companies, "contacts": contacts, "searches": searches}
