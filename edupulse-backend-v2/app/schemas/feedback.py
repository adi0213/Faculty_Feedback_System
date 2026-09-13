"""Pydantic schemas for feedback submission and status."""
from datetime import datetime
from typing import Annotated
from pydantic import BaseModel, Field, field_validator
import bleach


DIMENSIONS = frozenset(["clarity", "methodology", "punctuality", "fairness",
                         "approachability", "pacing", "engagement", "practical",
                         "assessment", "overall"])

MAX_COMMENT_LENGTH = 1000


class DimensionScore(BaseModel):
    """Single dimension score, enforced 1-4 Likert."""
    value: Annotated[int, Field(ge=1, le=4)]


class FeedbackSubmitRequest(BaseModel):
    """
    Student submits feedback for one faculty member.
    faculty_profile_id: the faculty's profile ID (not user ID).
    scores: dict mapping dimension names to 1-4 Likert values.
    comment: optional free text, max 1000 chars, sanitized server-side.
    sub_question_answers: answers to adaptive follow-up questions (optional).
    """
    faculty_profile_id: str = Field(min_length=36, max_length=36)
    term: str = Field(pattern=r"^\d{4}-S[12]$", example="2025-S2")
    scores: dict[str, Annotated[int, Field(ge=1, le=4)]] = Field(
        description="Dimension scores (1=poor, 4=excellent)"
    )
    comment: str | None = Field(default=None, max_length=MAX_COMMENT_LENGTH)
    sub_question_answers: list[dict] = Field(default_factory=list)

    @field_validator("scores")
    @classmethod
    def validate_dimensions(cls, v: dict) -> dict:
        unknown = set(v.keys()) - DIMENSIONS
        if unknown:
            raise ValueError(f"Unknown dimensions: {', '.join(unknown)}")
        return v

    @field_validator("comment")
    @classmethod
    def sanitize_comment(cls, v: str | None) -> str | None:
        if v is None:
            return None
        # Strip HTML tags, normalize whitespace
        cleaned = bleach.clean(v, tags=[], strip=True).strip()
        if len(cleaned) > MAX_COMMENT_LENGTH:
            cleaned = cleaned[:MAX_COMMENT_LENGTH]
        return cleaned if cleaned else None


class FeedbackStatusResponse(BaseModel):
    """Response for checking if a student has submitted feedback for a faculty."""
    submitted: bool
    term: str | None = None
    submitted_at: datetime | None = None


class FeedbackSubmitResponse(BaseModel):
    """Response after successful feedback submission."""
    success: bool = True
    message: str = "Feedback submitted successfully. Thank you!"
    nlp_queued: bool = True   # NLP processing queued in background


class FeedbackRecord(BaseModel):
    """Read-only view of a single feedback record (admin use only)."""
    id: str
    faculty_profile_id: str
    term: str
    sentiment_score: float | None = None
    sentiment_label: str | None = None
    topics: list[str] = Field(default_factory=list)
    is_spam: bool
    is_duplicate: bool
    is_constructive: bool
    nlp_processed: bool
    submitted_at: datetime

    model_config = {"from_attributes": True}
