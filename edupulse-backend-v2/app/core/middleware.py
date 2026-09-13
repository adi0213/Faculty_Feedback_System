"""
OWASP security headers, request ID injection, and structured request logging middleware.
"""
import time
import uuid
import logging

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adds OWASP-recommended security headers to every response.
    """
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        # Remove sensitive headers
        if "Server" in response.headers:
            del response.headers["Server"]
        if "X-Powered-By" in response.headers:
            del response.headers["X-Powered-By"]
        return response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Assigns a unique UUID to every request (X-Request-ID).
    Echoes back to client and uses in all log records for correlation.
    """
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs method, path, status code, duration, and request ID for every request.
    Never logs request bodies or Authorization headers.
    """
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start = time.perf_counter()
        request_id = getattr(request.state, "request_id", "-")

        response = await call_next(request)

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.info(
            "request",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "ip": request.client.host if request.client else "unknown",
            },
        )
        return response


def add_middlewares(app: FastAPI) -> None:
    """Register all middleware in correct order (outermost first)."""
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestIDMiddleware)
