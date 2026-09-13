"""
Audit logging service — writes structured, immutable audit records for every
state-changing operation.
"""
import json
import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


async def log_event(
    db: AsyncSession,
    *,
    event_type: str,
    event_outcome: str,
    user_id: str | None = None,
    user_role: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    request_id: str | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    """
    Write an audit log entry. Called from service layer after state changes.
    Failures are logged but never propagate — audit must not break business logic.
    """
    try:
        entry = AuditLog(
            user_id=user_id,
            user_role=user_role,
            event_type=event_type,
            event_outcome=event_outcome,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            details_json=json.dumps(details or {}),
        )
        db.add(entry)
        # Note: commit happens in the request's get_db session lifecycle
    except Exception as e:
        logger.error("Failed to write audit log entry: %s (event_type=%s)", e, event_type)


def audit_context_from_request(request: Any) -> dict[str, str | None]:
    """Extract audit context from a FastAPI Request object."""
    return {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("User-Agent"),
        "request_id": getattr(request.state, "request_id", None),
    }
