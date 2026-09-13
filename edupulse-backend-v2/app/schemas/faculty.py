"""Pydantic schemas for faculty profiles and dashboard data."""
from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field


class DimensionBreakdown(BaseModel):
    clarity: float | None = None
    methodology: float | None = None
    punctuality: float | None = None
    fairness: float | None = None
    approachability: float | None = None
    pacing: float | None = None
    engagement: float | None = None
    practical: float | None = None
    assessment: float | None = None
    overall: float | None = None


class ScoreTrendPoint(BaseModel):
    term: str
    composite_score: float
    response_count: int


class FacultyProfilePublic(BaseModel):
    """Public faculty profile shown on dashboards."""
    id: str
    faculty_code: str
    name: str
    dept: str
    subject: str | None = None
    college: str
    university: str
    response_count: int
    dimension_scores: DimensionBreakdown
    composite_score: float | None = None
    score_band: str | None = None  # strong | developing | needs_support
    score_trend: list[ScoreTrendPoint] = Field(default_factory=list)
    has_anomaly_flag: bool = False
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class FacultyDashboardData(FacultyProfilePublic):
    """Extended faculty data shown only on faculty's own dashboard."""
    is_k_anonymity_met: bool
    k_anonymity_threshold: int
    current_responses: int

    # NLP insights
    top_topics: list[str] = Field(default_factory=list)
    sentiment_summary: str | None = None  # "mostly positive" | "mixed" | "concerning"
    weak_dimensions: list[str] = Field(default_factory=list)
    strong_dimensions: list[str] = Field(default_factory=list)

    # Anomaly details
    anomaly_details: str | None = None


class FacultyListItem(BaseModel):
    """Faculty summary info for portal dashboards."""
    id: str
    user_id: str | None = None
    faculty_code: str
    name: str
    dept: str
    subject: str | None = None
    college: str
    university: str = "KTU"
    response_count: int
    dimension_scores: dict[str, float] | None = None
    composite_score: float | None = None
    score_band: str | None = None
    score_trend: list[ScoreTrendPoint] = Field(default_factory=list)
    has_anomaly_flag: bool = False

    model_config = {"from_attributes": True}
