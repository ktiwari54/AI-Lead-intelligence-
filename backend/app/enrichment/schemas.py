from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID


class EmailVerifyRequest(BaseModel):
    contact_id: UUID
    email: str


class EmailVerifyResponse(BaseModel):
    email: str
    status: str
    confidence: Optional[float] = None
    mx_record: Optional[bool] = None
    disposable: Optional[bool] = None
    free_provider: Optional[bool] = None


class BulkEnrichRequest(BaseModel):
    contact_ids: List[UUID]
    connector: str = "hunter"
