from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime


class SearchRequest(BaseModel):
    query: Optional[str] = None
    filters: Dict[str, Any] = {}
    search_type: str = "mixed"
    page: int = 1
    page_size: int = 20


class SearchOut(BaseModel):
    id: UUID
    query: Optional[str] = None
    filters: Dict[str, Any]
    search_type: str
    status: str
    result_count: int
    execution_time_ms: Optional[int] = None
    created_at: datetime
    model_config = {"from_attributes": True}


class SavedSearchCreate(BaseModel):
    name: str
    query: Optional[str] = None
    filters: Dict[str, Any] = {}
    search_type: str = "mixed"
    alert_enabled: bool = False
    alert_frequency: Optional[str] = None


class SavedSearchOut(BaseModel):
    id: UUID
    name: str
    query: Optional[str] = None
    filters: Dict[str, Any]
    search_type: Optional[str] = None
    created_at: datetime
    model_config = {"from_attributes": True}
