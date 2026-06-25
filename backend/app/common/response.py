from typing import Any, Generic, TypeVar
from pydantic import BaseModel
import math

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T | None = None
    message: str | None = None


class PaginatedResponse(BaseModel, Generic[T]):
    success: bool = True
    data: list[T]
    total: int
    page: int
    per_page: int
    pages: int

    @classmethod
    def create(cls, data: list[T], total: int, page: int, per_page: int) -> "PaginatedResponse[T]":
        pages = math.ceil(total / per_page) if per_page > 0 else 0
        return cls(data=data, total=total, page=page, per_page=per_page, pages=pages)
