"""Application exception hierarchy and FastAPI exception handlers."""
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import ORJSONResponse
from jose import JWTError


class AppException(Exception):
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    code: str = "internal_error"
    message: str = "An unexpected error occurred"

    def __init__(self, message: str | None = None, details: Any = None) -> None:
        self.message = message or self.__class__.message
        self.details = details
        super().__init__(self.message)


class NotFoundError(AppException):
    status_code = status.HTTP_404_NOT_FOUND
    code = "not_found"
    message = "Resource not found"


class ValidationError(AppException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    code = "validation_error"
    message = "Validation failed"


class AuthenticationError(AppException):
    status_code = status.HTTP_401_UNAUTHORIZED
    code = "unauthorized"
    message = "Authentication required"


class AuthorizationError(AppException):
    status_code = status.HTTP_403_FORBIDDEN
    code = "forbidden"
    message = "Insufficient permissions"


class ConflictError(AppException):
    status_code = status.HTTP_409_CONFLICT
    code = "conflict"
    message = "Resource already exists"


class RateLimitError(AppException):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    code = "rate_limit_exceeded"
    message = "Too many requests"


class InsufficientCreditsError(AppException):
    status_code = status.HTTP_402_PAYMENT_REQUIRED
    code = "insufficient_credits"
    message = "Insufficient credits"


class SubscriptionLimitError(AppException):
    status_code = status.HTTP_402_PAYMENT_REQUIRED
    code = "subscription_limit"
    message = "Subscription limit reached"


class ConnectorError(AppException):
    status_code = status.HTTP_502_BAD_GATEWAY
    code = "connector_error"
    message = "Connector request failed"


def _error_response(request: Request, exc: AppException) -> ORJSONResponse:
    return ORJSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
                "request_id": getattr(request.state, "request_id", None),
            }
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> ORJSONResponse:
        return _error_response(request, exc)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> ORJSONResponse:
        return ORJSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "validation_error",
                    "message": "Request validation failed",
                    "details": exc.errors(),
                    "request_id": getattr(request.state, "request_id", None),
                }
            },
        )

    @app.exception_handler(JWTError)
    async def jwt_exception_handler(request: Request, exc: JWTError) -> ORJSONResponse:
        return ORJSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error": {"code": "invalid_token", "message": "Invalid or expired token"}},
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> ORJSONResponse:
        return ORJSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": {"code": "internal_error", "message": "An unexpected error occurred"}},
        )
