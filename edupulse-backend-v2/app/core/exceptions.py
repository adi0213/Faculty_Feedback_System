"""
Custom exception types and global FastAPI exception handlers.
Returns structured, safe error responses that never leak internal details.
"""
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import ORJSONResponse


class AppError(Exception):
    """Base application exception with HTTP status code and client-safe message."""

    def __init__(self, message: str, status_code: int = 500, details: Any = None):
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class AuthenticationError(AppError):
    def __init__(self, message: str = "Authentication required"):
        super().__init__(message, status_code=status.HTTP_401_UNAUTHORIZED)


class AuthorizationError(AppError):
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, status_code=status.HTTP_403_FORBIDDEN)


class NotFoundError(AppError):
    def __init__(self, resource: str = "Resource"):
        super().__init__(f"{resource} not found", status_code=status.HTTP_404_NOT_FOUND)


class ConflictError(AppError):
    def __init__(self, message: str = "Resource already exists"):
        super().__init__(message, status_code=status.HTTP_409_CONFLICT)


class ValidationError(AppError):
    def __init__(self, message: str, details: Any = None):
        super().__init__(message, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, details=details)


class RateLimitError(AppError):
    def __init__(self, message: str = "Rate limit exceeded. Please try again later."):
        super().__init__(message, status_code=status.HTTP_429_TOO_MANY_REQUESTS)


class FeedbackAlreadySubmittedError(ConflictError):
    def __init__(self):
        super().__init__("Feedback for this faculty has already been submitted this term.")


class KAnonymityNotMetError(AppError):
    def __init__(self, current: int, required: int):
        super().__init__(
            f"Report not available yet. Requires {required} responses; {current} received so far.",
            status_code=status.HTTP_425_TOO_EARLY,
            details={"current_responses": current, "required_responses": required},
        )


def _error_response(status_code: int, message: str, details: Any = None) -> ORJSONResponse:
    body: dict[str, Any] = {"error": message, "status": status_code}
    if details:
        body["details"] = details
    return ORJSONResponse(status_code=status_code, content=body)


def register_exception_handlers(app: FastAPI) -> None:
    """Attach all exception handlers to the FastAPI app."""

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> ORJSONResponse:
        return _error_response(exc.status_code, exc.message, exc.details)

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError) -> ORJSONResponse:
        # Summarize validation errors without leaking internal field paths in production
        errors = [
            {"field": ".".join(str(loc) for loc in e["loc"]), "message": e["msg"]}
            for e in exc.errors()
        ]
        return _error_response(422, "Request validation failed", errors)

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception) -> ORJSONResponse:
        # Never expose internal stack traces to clients
        import logging
        logging.getLogger(__name__).exception("Unhandled exception: %s", exc)
        return _error_response(500, "An internal error occurred. Please try again later.")
