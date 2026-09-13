"""Pydantic schemas for course recommendations and improvement roadmaps."""
from datetime import datetime
from pydantic import BaseModel, Field


class EvidenceItem(BaseModel):
    """A piece of evidence supporting a recommendation."""
    source: str        # "sentiment_analysis" | "absa" | "topic_model" | "likert_score"
    dimension: str
    description: str
    weight: float      # 0.0–1.0, how strongly this evidence supports the recommendation


class CourseRecommendationResponse(BaseModel):
    """A single course recommendation with full justification."""
    id: str
    course_id: str | None = None
    course_title: str
    provider: str       # NPTEL | SWAYAM | AICTE | UGC
    institution: str | None = None
    url: str | None = None
    duration_label: str | None = None

    target_dimension: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    similarity_score: float | None = Field(default=None, ge=0.0, le=1.0)

    evidence: list[EvidenceItem] = Field(default_factory=list)
    justification: str
    learning_outcomes: str | None = None
    expected_impact: str | None = None

    is_accepted: bool | None = None  # None = not reviewed
    created_at: datetime

    model_config = {"from_attributes": True}


class RoadmapWeek(BaseModel):
    week_number: int
    title: str
    phase: str         # e.g. "Foundation" | "Practice" | "Reflect"
    goals: list[str]
    actions: list[str]
    success_metrics: list[str]


class RoadmapPhase(BaseModel):
    """30, 60, or 90-day phase."""
    phase_label: str   # "30-Day" | "60-Day" | "90-Day"
    theme: str
    focus_dimensions: list[str]
    weeks: list[RoadmapWeek]
    milestone: str


class FacultyRoadmapResponse(BaseModel):
    """Complete 30/60/90-day improvement roadmap for a faculty member."""
    id: str
    faculty_profile_id: str
    term: str
    score_band: str
    composite_score: float

    executive_summary: str | None = None
    root_cause_analysis: str | None = None

    day30: RoadmapPhase | None = None
    day60: RoadmapPhase | None = None
    day90: RoadmapPhase | None = None

    recommended_courses: list[CourseRecommendationResponse] = Field(default_factory=list)

    progress_percent: int = 0
    is_published: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
