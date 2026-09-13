"""
SQLAlchemy ORM models — User and identity-related tables.
These live in the 'registry' schema and are never joined to feedback tables
in the AI/analytics pipeline.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, Index, Integer,
    String, Text, UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db.session import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    """
    Core user table. Stores all portal users (students, faculty, hod,
    principal, university admin). Passwords are bcrypt-hashed at service layer.
    """
    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_email", "email", unique=True),
        Index("ix_users_role", "role"),
        {"schema": "registry"},
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    role = Column(
        Enum("student", "faculty", "hod", "principal", "university", "admin",
             name="user_role_enum", schema="registry"),
        nullable=False,
        index=True,
    )
    name = Column(String(200), nullable=False)
    email = Column(String(320), nullable=False, unique=True)
    hashed_password = Column(String(128), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Academic context
    dept = Column(String(100), nullable=True)
    semester = Column(Integer, nullable=True)
    college = Column(String(200), nullable=True)
    university = Column(String(200), nullable=True)

    # Student-specific: JSON array of faculty IDs enrolled with this term
    enrolled_faculty_ids = Column(Text, nullable=True)  # JSON string

    # Audit fields
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    issued_tokens = relationship("PseudoToken", back_populates="user", cascade="all, delete-orphan")
    roadmaps = relationship(
        "FacultyRoadmap",
        back_populates="faculty_user",
        primaryjoin="User.id == FacultyRoadmap.faculty_id",
        foreign_keys="FacultyRoadmap.faculty_id",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} role={self.role} email={self.email}>"
