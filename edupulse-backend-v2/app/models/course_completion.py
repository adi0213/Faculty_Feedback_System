"""SQLAlchemy model for faculty course completion (certificate uploads)."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, Index
from app.db.session import Base


def _now():
    return datetime.now(timezone.utc)


class CourseCompletion(Base):
    __tablename__ = "course_completions"

    id                   = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    faculty_profile_id   = Column(String, nullable=False, index=True)   # No FK — cross-schema SQLite
    course_key           = Column(String, nullable=False)
    course_name          = Column(String, nullable=False)
    provider             = Column(String, nullable=False)
    dimension_id         = Column(String, nullable=False)
    certificate_filename = Column(String, nullable=True)
    certificate_url      = Column(String, nullable=True)
    score_boost          = Column(Float, default=0.15, nullable=False)
    completed_at         = Column(DateTime(timezone=True), default=_now, nullable=False)
    created_at           = Column(DateTime(timezone=True), default=_now, nullable=False)
