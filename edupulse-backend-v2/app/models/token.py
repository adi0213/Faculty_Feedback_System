"""
Pseudonymous token model — maps a one-time HMAC-derived token back
to a (student, faculty, term) triple. Held separately from feedback tables.
Only the Token Service and the enrollment verification step have access.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.session import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PseudoToken(Base):
    """
    One row per (user_id, faculty_profile_id, term) triple.
    The 'token_hash' field is stored (SHA-256 of the HMAC token),
    not the token itself — so a DB breach doesn't reveal the linking secret.
    """
    __tablename__ = "pseudo_tokens"
    __table_args__ = (
        UniqueConstraint("user_id", "faculty_profile_id", "term",
                         name="uq_token_per_student_faculty_term"),
        Index("ix_pseudo_tokens_token_hash", "token_hash"),
        {"schema": "registry"},
    )

    id: str = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: str = Column(String(36), ForeignKey("registry.users.id", ondelete="CASCADE"), nullable=False)
    faculty_profile_id: str = Column(String(36), nullable=False)
    term: str = Column(String(20), nullable=False)

    # SHA-256 hash of the HMAC token — stored for lookup, never the raw token
    token_hash: str = Column(String(64), nullable=False, unique=True)

    is_used: bool = Column(Boolean, default=False, nullable=False)
    created_at: datetime = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    used_at: datetime | None = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="issued_tokens")
