"""Recommendations router — AI course recommendations and roadmaps."""
import json
import logging
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import require_role
from app.models.faculty import FacultyProfile
from app.models.roadmap import CourseRecommendation, FacultyRoadmap
from app.services.recommendation_service import (
    generate_faculty_recommendations,
    generate_faculty_roadmap,
)

router = APIRouter(prefix="/recommendations", tags=["Recommendations & Roadmaps"])
logger = logging.getLogger(__name__)


def _parse_json(text: str | None, default):
    if not text:
        return default
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return default


@router.post(
    "/generate/{faculty_profile_id}",
    summary="Generate AI course recommendations for a faculty member",
)
async def generate_recommendations(
    faculty_profile_id: str,
    term: str = Query(default="2025-S2"),
    db: AsyncSession = Depends(get_db),
    user=Depends(require_role("faculty", "hod", "principal", "admin")),
):
    """
    Triggers the full RAG + LLM recommendation pipeline.
    Faculty can request for themselves; HoD/Principal can request for their scope.
    """
    # Scope check: faculty can only generate their own
    if user.role == "faculty":
        result = await db.execute(
            select(FacultyProfile).where(
                FacultyProfile.id == faculty_profile_id,
                FacultyProfile.user_id == user.id,
            )
        )
        if not result.scalar_one_or_none():
            from app.core.exceptions import AuthorizationError
            raise AuthorizationError("You can only generate recommendations for yourself")

    recs = await generate_faculty_recommendations(db, faculty_profile_id, term)
    return {
        "message": f"Generated {len(recs)} recommendations",
        "count": len(recs),
        "faculty_profile_id": faculty_profile_id,
    }


@router.get(
    "/{faculty_profile_id}",
    summary="Get existing recommendations for a faculty member",
)
async def get_recommendations(
    faculty_profile_id: str,
    term: str = Query(default="2025-S2"),
    db: AsyncSession = Depends(get_db),
    user=Depends(require_role("faculty", "hod", "principal", "admin")),
):
    """Get persisted recommendations for a faculty/term."""
    result = await db.execute(
        select(CourseRecommendation).where(
            CourseRecommendation.faculty_profile_id == faculty_profile_id,
            CourseRecommendation.term == term,
        )
    )
    recs = result.scalars().all()
    return [
        {
            "id": r.id,
            "target_dimension": r.target_dimension,
            "confidence_score": r.confidence_score,
            "evidence": _parse_json(r.evidence_json, []),
            "justification": r.justification_text,
            "learning_outcomes": r.learning_outcomes_text,
            "expected_impact": r.expected_impact_text,
            "is_accepted": r.is_accepted,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in recs
    ]


@router.post(
    "/roadmap/generate/{faculty_profile_id}",
    summary="Generate 30/60/90-day improvement roadmap",
)
async def generate_roadmap_endpoint(
    faculty_profile_id: str,
    term: str = Query(default="2025-S2"),
    db: AsyncSession = Depends(get_db),
    user=Depends(require_role("faculty", "hod", "admin")),
):
    """Generate a personalized roadmap. Faculty can only request their own."""
    if user.role == "faculty":
        fac_result = await db.execute(
            select(FacultyProfile).where(
                FacultyProfile.id == faculty_profile_id,
                FacultyProfile.user_id == user.id,
            )
        )
        if not fac_result.scalar_one_or_none():
            from app.core.exceptions import AuthorizationError
            raise AuthorizationError("You can only generate a roadmap for yourself")

    roadmap = await generate_faculty_roadmap(db, faculty_profile_id, user.id, term)
    return {
        "message": "Roadmap generated successfully",
        "roadmap_id": roadmap.id,
        "faculty_profile_id": faculty_profile_id,
    }


@router.get(
    "/roadmap/{faculty_profile_id}",
    summary="Get the latest roadmap for a faculty member",
)
async def get_roadmap(
    faculty_profile_id: str,
    term: str = Query(default="2025-S2"),
    db: AsyncSession = Depends(get_db),
    user=Depends(require_role("faculty", "hod", "principal", "admin")),
):
    """Returns the latest published roadmap for the faculty/term."""
    result = await db.execute(
        select(FacultyRoadmap).where(
            FacultyRoadmap.faculty_profile_id == faculty_profile_id,
            FacultyRoadmap.term == term,
        ).order_by(FacultyRoadmap.created_at.desc())
    )
    roadmap = result.scalars().first()
    if not roadmap:
        return {"message": "No roadmap generated yet for this faculty/term"}

    return {
        "id": roadmap.id,
        "term": roadmap.term,
        "score_band": roadmap.score_band,
        "composite_score": roadmap.composite_score,
        "executive_summary": roadmap.executive_summary,
        "root_cause_analysis": roadmap.root_cause_analysis,
        "day30": _parse_json(roadmap.day30_plan_json, {}),
        "day60": _parse_json(roadmap.day60_plan_json, {}),
        "day90": _parse_json(roadmap.day90_plan_json, {}),
        "progress_percent": roadmap.progress_percent,
        "is_published": roadmap.is_published,
        "created_at": roadmap.created_at.isoformat() if roadmap.created_at else None,
    }
