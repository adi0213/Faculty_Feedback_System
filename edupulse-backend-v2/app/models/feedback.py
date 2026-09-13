"""
Feedback record model — anonymous, codes-only. No student identity stored here.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey,
    Index, Integer, String, Text, CheckConstraint,
)
from sqlalchemy.orm import relationship

from app.db.session import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class FeedbackRecord(Base):
    """
    Stores one anonymous feedback submission. Contains only:
    - pseudonymous token (not reversible to student without HMAC key)
    - faculty_profile_id (links to faculty, not to student)
    - structured Likert scores (JSON)
    - optional free-text comment (already sanitized at ingestion)
    - NLP analysis results
    """
    __tablename__ = "feedback_records"
    __table_args__ = (
        Index("ix_feedback_faculty_term", "faculty_profile_id", "term"),
        Index("ix_feedback_submitted_at", "submitted_at"),
        Index("ix_feedback_token", "student_token"),
        CheckConstraint("length(student_token) > 0", name="ck_feedback_token_nonempty"),
        {"schema": "feedback"},
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Anonymization: HMAC-derived token, one per (student, faculty, term)
    student_token = Column(String(64), nullable=False)

    faculty_profile_id = Column(
        String(36),
        ForeignKey("feedback.faculty_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    term = Column(String(20), nullable=False)  # e.g. "2025-S2"
    course_code = Column(String(50), nullable=True)

    # ── Structured scores (stored as JSON for flexibility) ────────────────
    # {"clarity": 4, "methodology": 2, "punctuality": 3, ...}  (1–4 scale)
    scores_json = Column(Text, nullable=False)

    # Optional free-text comment (sanitized, max 1000 chars)
    comment_raw = Column(Text, nullable=True)         # Original (sanitized) text
    comment_language = Column(String(10), nullable=True)  # 'en' | 'ml' | 'mixed'

    # ── NLP analysis results ──────────────────────────────────────────────
    sentiment_score = Column(Float, nullable=True)    # -1.0 to +1.0
    sentiment_label = Column(String(20), nullable=True)  # positive|negative|neutral

    # Aspect-based sentiment: {"clarity": 0.8, "methodology": -0.5, ...}
    absa_scores_json = Column(Text, nullable=True)

    # Topics extracted from comment (JSON array of strings)
    topics_json = Column(Text, nullable=True)

    # Dimensions flagged by comment (JSON array: ["clarity", "pacing"])
    flagged_dimensions_json = Column(Text, nullable=True)

    # ── Quality flags ────────────────────────────────────────────────────
    is_spam = Column(Boolean, default=False, nullable=False)
    is_duplicate = Column(Boolean, default=False, nullable=False)
    duplicate_of_id = Column(String(36), nullable=True)
    is_constructive = Column(Boolean, default=True, nullable=False)
    is_temporal_anomaly = Column(Boolean, default=False, nullable=False)

    # Processing status
    nlp_processed = Column(Boolean, default=False, nullable=False)
    nlp_processed_at = Column(DateTime(timezone=True), nullable=True)

    submitted_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    # Relationships
    faculty = relationship("FacultyProfile", back_populates="feedback_records")

    def __repr__(self) -> str:
        return f"<FeedbackRecord id={self.id} faculty={self.faculty_profile_id} term={self.term}>"


class SubmissionRecord(Base):
    """
    Deduplication table: records which (student_token, faculty_profile_id, term)
    combinations have been submitted. Prevents double-submission.
    The student_token is derived from the student's ID via HMAC but is
    not reversible here.
    """
    __tablename__ = "submission_records"
    __table_args__ = (
        Index(
            "uix_submission_token_faculty_term",
            "student_token", "faculty_profile_id", "term",
            unique=True,
        ),
        {"schema": "feedback"},
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_token = Column(String(64), nullable=False)
    faculty_profile_id = Column(String(36), nullable=False)
    term = Column(String(20), nullable=False)
    submitted_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
