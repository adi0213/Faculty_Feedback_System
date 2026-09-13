"""SQLAlchemy model for faculty course completion (certificate uploads)."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, Index
from app.db.session import Base


def _now():
    return datetime.now(timezone.utc)


class CourseCompletion(Base):
    __tablename__ = "course_completions"

    id: str = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    faculty_profile_id: str = Column(String, nullable=False, index=True)   # No FK — cross-schema SQLite
    course_key: str = Column(String, nullable=False)
    course_name: str = Column(String, nullable=False)
    provider: str = Column(String, nullable=False)
    dimension_id: str = Column(String, nullable=False)
    certificate_filename: str | None = Column(String, nullable=True)
    certificate_url: str | None = Column(String, nullable=True)
    score_boost: float = Column(Float, default=0.15, nullable=False)
    completed_at: datetime = Column(DateTime(timezone=True), default=_now, nullable=False)
    created_at: datetime = Column(DateTime(timezone=True), default=_now, nullable=False)
