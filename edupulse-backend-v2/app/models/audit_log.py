"""
Audit log model — immutable record of all state-changing operations.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Index, Integer, String, Text
from app.db.session import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AuditLog(Base):
    """
    Append-only audit trail. Never updated or deleted.
    Records: who did what, on which resource, from which IP, at what time.
    """
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_user_id", "user_id"),
        Index("ix_audit_event_type", "event_type"),
        Index("ix_audit_created_at", "created_at"),
        {"schema": "registry"},
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(36), default=lambda: str(uuid.uuid4()), unique=True)

    # Actor (nullable for unauthenticated events like failed logins)
    user_id = Column(String(36), nullable=True)
    user_role = Column(String(50), nullable=True)

    # Event classification
    event_type = Column(String(100), nullable=False)  # e.g. "feedback.submit", "auth.login"
    event_outcome = Column(String(20), nullable=False)  # success | failure | blocked

    # Resource
    resource_type = Column(String(100), nullable=True)  # "feedback" | "faculty" | "user"
    resource_id = Column(String(36), nullable=True)

    # Context
    ip_address = Column(String(45), nullable=True)   # IPv4 or IPv6
    user_agent = Column(Text, nullable=True)
    request_id = Column(String(36), nullable=True)   # Correlates to X-Request-ID header

    # Payload (sanitized — no PII, no raw comments)
    details_json = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<AuditLog {self.event_type} by {self.user_id} @ {self.created_at}>"
