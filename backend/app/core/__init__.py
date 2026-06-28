"""Phase 3 application kernel — cross-cutting concerns."""

from backend.app.core.context import RequestContext
from backend.app.core.exceptions import AppException, ErrorDetail, ErrorResponse

__all__ = [
    "AppException",
    "ErrorDetail",
    "ErrorResponse",
    "RequestContext",
]