from fastapi import Query
from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1, description="Page number")
    per_page: int = Field(default=25, ge=1, le=100, description="Results per page")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.per_page


def pagination_params(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=25, ge=1, le=100),
) -> PaginationParams:
    return PaginationParams(page=page, per_page=per_page)
