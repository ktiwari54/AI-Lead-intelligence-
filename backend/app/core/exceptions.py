from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: list[dict[str, Any]] = Field(default_factory=list)
    request_id: str | None = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail


class AppException(Exception):
    """Base application exception mapped to HTTP responses."""

    status_code: int = 500
    code: str = "INTERNAL_ERROR"

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        details: list[dict[str, Any]] | None = None,
    ):
        super().__init__(message)
        self.message = message
        if code:
            self.code = code
        self.details = details or []


class NotFoundException(AppException):
    status_code = 404
    code = "NOT_FOUND"


class UnauthorizedException(AppException):
    status_code = 401
    code = "UNAUTHORIZED"


class ForbiddenException(AppException):
    status_code = 403
    code = "FORBIDDEN"


class ConflictException(AppException):
    status_code = 409
    code = "CONFLICT"


class ValidationException(AppException):
    status_code = 400
    code = "VALIDATION_ERROR"


class InsufficientCreditsException(AppException):
    status_code = 402
    code = "INSUFFICIENT_CREDITS"


class RateLimitedException(AppException):
    status_code = 429
    code = "RATE_LIMITED"