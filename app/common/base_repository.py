"""Generic async repository using SQLAlchemy 2.x."""
from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy import func, select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

ModelT = TypeVar("ModelT")


class BaseRepository(Generic[ModelT]):
    model: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, id: UUID) -> ModelT | None:
        result = await self.session.get(self.model, id)
        return result

    async def get_or_raise(self, id: UUID) -> ModelT:
        obj = await self.get(id)
        if obj is None:
            from app.core.exceptions import NotFoundError
            raise NotFoundError(f"{self.model.__name__} {id} not found")
        return obj

    async def list(
        self,
        *,
        filters: dict[str, Any] | None = None,
        offset: int = 0,
        limit: int = 25,
        order_by: Any = None,
    ) -> tuple[list[ModelT], int]:
        stmt = select(self.model)
        if filters:
            for k, v in filters.items():
                stmt = stmt.where(getattr(self.model, k) == v)
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.session.execute(count_stmt)).scalar_one()
        if order_by is not None:
            stmt = stmt.order_by(order_by)
        stmt = stmt.offset(offset).limit(limit)
        rows = (await self.session.execute(stmt)).scalars().all()
        return list(rows), total

    async def create(self, **kwargs: Any) -> ModelT:
        obj = self.model(**kwargs)
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def update(self, id: UUID, **kwargs: Any) -> ModelT:
        obj = await self.get_or_raise(id)
        for k, v in kwargs.items():
            setattr(obj, k, v)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def delete(self, id: UUID) -> None:
        obj = await self.get_or_raise(id)
        await self.session.delete(obj)
        await self.session.flush()

    async def soft_delete(self, id: UUID) -> ModelT:
        from datetime import datetime, timezone
        return await self.update(id, deleted_at=datetime.now(timezone.utc))

    async def count(self, **filters: Any) -> int:
        stmt = select(func.count()).select_from(self.model)
        for k, v in filters.items():
            stmt = stmt.where(getattr(self.model, k) == v)
        return (await self.session.execute(stmt)).scalar_one()
