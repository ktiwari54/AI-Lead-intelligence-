from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.crm import Activity, Note, Tag, Task
from app.crm.schemas import ActivityCreate, NoteCreate, TagCreate, TaskCreate


async def create_activity(data: ActivityCreate, org_id: UUID, user_id: UUID, db: AsyncSession) -> Activity:
    activity = Activity(**data.model_dump(exclude_none=True), organization_id=org_id, created_by=user_id)
    db.add(activity)
    await db.flush()
    return activity


async def create_note(data: NoteCreate, org_id: UUID, user_id: UUID, db: AsyncSession) -> Note:
    note = Note(**data.model_dump(exclude_none=True), organization_id=org_id, created_by=user_id)
    db.add(note)
    await db.flush()
    return note


async def list_tags(org_id: UUID, db: AsyncSession):
    return (await db.execute(select(Tag).where(Tag.organization_id == org_id, Tag.is_deleted == False))).scalars().all()


async def create_tag(data: TagCreate, org_id: UUID, db: AsyncSession) -> Tag:
    tag = Tag(**data.model_dump(exclude_none=True), organization_id=org_id)
    db.add(tag)
    await db.flush()
    return tag


async def create_task(data: TaskCreate, org_id: UUID, user_id: UUID, db: AsyncSession) -> Task:
    task = Task(**data.model_dump(exclude_none=True), organization_id=org_id, created_by=user_id)
    db.add(task)
    await db.flush()
    return task
