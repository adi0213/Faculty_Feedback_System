"""
Faculty profile model — academic details, aggregated scores, and trend data.
Kept in 'feedback' schema. Identified by an opaque faculty_code, not a name,
when passed to the AI pipeline.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, Column, DateTime, Float, Index,
    Integer, String, Text,
)
from sqlalchemy.orm import relationship

from app.db.session import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class FacultyProfile(Base):
    """
    Stores per-faculty academic metadata and aggregated feedback scores.
    The 'user_id' links to registry.users for login, but the AI pipeline
    should only receive 'faculty_code' (opaque), never 'user_id'.
    """
    __tablename__ = "faculty_profiles"
    __table_args__ = (
        Index("ix_faculty_profiles_user_id", "user_id", unique=True),
        Index("ix_faculty_profiles_dept_college", "dept", "college"),
        {"schema": "feedback"},
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, unique=True)  # FK to registry.users (not enforced cross-schema)
    faculty_code = Column(String(20), nullable=False, unique=True)  # Opaque: FAC-NNNN
    name = Column(String(200), nullable=False)
    dept = Column(String(100), nullable=False)
    subject = Column(String(200), nullable=True)
    college = Column(String(200), nullable=False)
    university = Column(String(200), nullable=False, default="KTU")

    # Aggregated statistics (recomputed by scoring engine after each batch)
    response_count = Column(Integer, default=0, nullable=False)

    # Per-dimension running means (JSON: {"clarity": 3.8, ...})
    dimension_scores_json = Column(Text, default="{}", nullable=False)

    # Historical composite scores per term (JSON: [{"term": "2024-S1", "score": 3.6}, ...])
    score_trend_json = Column(Text, default="[]", nullable=False)

    # Current composite (Empirical Bayes shrunk, Winsorized)
    composite_score = Column(Float, nullable=True)
    score_band = Column(String(20), nullable=True)  # strong | developing | needs_support

    # Flags
    has_anomaly_flag = Column(Boolean, default=False)
    anomaly_details_json = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    # Relationships
    feedback_records = relationship("FeedbackRecord", back_populates="faculty", cascade="all, delete-orphan")
    roadmaps = relationship("FacultyRoadmap", back_populates="faculty_profile", foreign_keys="FacultyRoadmap.faculty_profile_id")
    recommendations = relationship("CourseRecommendation", back_populates="faculty", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<FacultyProfile code={self.faculty_code} dept={self.dept}>"
