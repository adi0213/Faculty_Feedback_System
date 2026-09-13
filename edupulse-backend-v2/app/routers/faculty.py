"""Faculty router — profile, dashboard data, faculty list for admin roles."""
import json
import logging
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.session import get_db
from app.dependencies import get_current_user, require_role
from app.models.faculty import FacultyProfile
from app.schemas.faculty import FacultyDashboardData, FacultyListItem, FacultyProfilePublic, ScoreTrendPoint, DimensionBreakdown
from app.services.analytics_service import get_faculty_trend
from app.services.feedback_service import get_feedback_count

router = APIRouter(prefix="/faculty", tags=["Faculty"])
logger = logging.getLogger(__name__)
settings = get_settings()


def _parse_json(text, default):
    if not text:
        return default
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return default


def _to_profile_public(f: FacultyProfile, trend=None) -> FacultyProfilePublic:
    dim_scores = _parse_json(f.dimension_scores_json, {})
    trend_data = trend or _parse_json(f.score_trend_json, [])
    valid_dims = {k: v for k, v in dim_scores.items() if k in DimensionBreakdown.model_fields}
    return FacultyProfilePublic(
        id=f.id,
        faculty_code=f.faculty_code,
        name=f.name,
        dept=f.dept,
        subject=f.subject,
        college=f.college,
        university=f.university,
        response_count=f.response_count,
        dimension_scores=DimensionBreakdown(**valid_dims),
        composite_score=f.composite_score,
        score_band=f.score_band,
        score_trend=[
            ScoreTrendPoint(**t)
            for t in trend_data
            if all(k in t for k in ["term", "composite_score", "response_count"])
        ],
        has_anomaly_flag=f.has_anomaly_flag,
        updated_at=f.updated_at,
    )


@router.get("/me", response_model=FacultyDashboardData, summary="Faculty's own dashboard")
async def get_my_dashboard(
    term: str = Query(default="2025-S2", pattern=r"^\d{4}-S[12]$"),
    db: AsyncSession = Depends(get_db),
    user=Depends(require_role("faculty")),
):
    """
    Returns the full faculty dashboard including scores, NLP insights,
    and AI readiness indicators. Only accessible to the faculty themselves.
    """
    result = await db.execute(
        select(FacultyProfile).where(FacultyProfile.user_id == user.id)
    )
    faculty = result.scalar_one_or_none()
    if not faculty:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Faculty profile")

    n = await get_feedback_count(db, faculty.id, term)
    k = settings.k_anonymity_threshold
    dim_scores = _parse_json(faculty.dimension_scores_json, {})
    trend = await get_faculty_trend(db, faculty.id)

    weak = sorted(
        [d for d, v in dim_scores.items() if isinstance(v, (int, float)) and v < 3.0],
        key=lambda d: dim_scores.get(d, 0),
    )
    strong = [d for d, v in dim_scores.items() if isinstance(v, (int, float)) and v >= 4.0]

    profile = _to_profile_public(faculty, [t.__dict__ for t in trend])

    return FacultyDashboardData(
        **profile.model_dump(),
        is_k_anonymity_met=(n >= k),
        k_anonymity_threshold=k,
        current_responses=n,
        weak_dimensions=weak[:3],
        strong_dimensions=strong[:3],
        sentiment_summary=None,
        anomaly_details=_parse_json(faculty.anomaly_details_json, {}).get("details"),
    )


@router.get(
    "/list",
    response_model=list[FacultyListItem],
    summary="List faculties (All authenticated users)",
)
async def list_faculties(
    college: str | None = Query(default=None),
    dept: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    user=Depends(require_role("student", "faculty", "hod", "principal", "university", "admin")),
):
    """Returns faculty list scoped to the caller's access level."""
    query = select(FacultyProfile)

    if user.role == "hod":
        query = query.where(FacultyProfile.dept == user.dept, FacultyProfile.college == user.college)
    elif user.role == "principal":
        query = query.where(FacultyProfile.college == user.college)
    elif user.role == "university":
        if college:
            query = query.where(FacultyProfile.college == college)
        if dept:
            query = query.where(FacultyProfile.dept == dept)

    result = await db.execute(query)
    faculties = result.scalars().all()

    items = []
    for f in faculties:
        dim_scores = _parse_json(f.dimension_scores_json, {})
        trend_data = _parse_json(f.score_trend_json, [])
        items.append(
            FacultyListItem(
                id=f.id,
                user_id=f.user_id,
                faculty_code=f.faculty_code,
                name=f.name,
                dept=f.dept,
                subject=f.subject,
                college=f.college,
                university=f.university,
                response_count=f.response_count,
                dimension_scores=dim_scores,
                composite_score=f.composite_score,
                score_band=f.score_band,
                score_trend=[
                    ScoreTrendPoint(**t)
                    for t in trend_data
                    if isinstance(t, dict) and all(k in t for k in ["term", "composite_score", "response_count"])
                ],
                has_anomaly_flag=f.has_anomaly_flag,
            )
        )

    return items


@router.get(
    "/{faculty_id}",
    response_model=FacultyProfilePublic,
    summary="Get faculty profile (admin roles)",
)
async def get_faculty_profile(
    faculty_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_role("hod", "principal", "university", "admin")),
):
    """Get full faculty profile. Accessible by HoD, Principal, University, and Admin."""
    result = await db.execute(select(FacultyProfile).where(FacultyProfile.id == faculty_id))
    faculty = result.scalar_one_or_none()
    if not faculty:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Faculty profile")
    trend = await get_faculty_trend(db, faculty.id)
    return _to_profile_public(faculty, [t.__dict__ for t in trend])
