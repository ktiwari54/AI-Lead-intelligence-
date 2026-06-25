from fastapi import APIRouter, Depends
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.common.dependencies import get_current_user, get_current_org
from app.crm import service
from app.crm.schemas import ActivityCreate, ActivityOut, NoteCreate, NoteOut, TagCreate, TagOut, TaskCreate, TaskOut

router = APIRouter()


@router.post("/activities", response_model=ActivityOut, status_code=201)
async def create_activity(data: ActivityCreate, db: AsyncSession = Depends(get_db), user=Depends(get_current_user), org=Depends(get_current_org)):
    return await service.create_activity(data, org.id, user.id, db)


@router.post("/notes", response_model=NoteOut, status_code=201)
async def create_note(data: NoteCreate, db: AsyncSession = Depends(get_db), user=Depends(get_current_user), org=Depends(get_current_org)):
    return await service.create_note(data, org.id, user.id, db)


@router.get("/tags", response_model=List[TagOut])
async def list_tags(db: AsyncSession = Depends(get_db), org=Depends(get_current_org)):
    return await service.list_tags(org.id, db)


@router.post("/tags", response_model=TagOut, status_code=201)
async def create_tag(data: TagCreate, db: AsyncSession = Depends(get_db), org=Depends(get_current_org)):
    return await service.create_tag(data, org.id, db)


@router.post("/tasks", response_model=TaskOut, status_code=201)
async def create_task(data: TaskCreate, db: AsyncSession = Depends(get_db), user=Depends(get_current_user), org=Depends(get_current_org)):
    return await service.create_task(data, org.id, user.id, db)
