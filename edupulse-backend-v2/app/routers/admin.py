"""Admin router — audit log, user management, system operations."""
import logging
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import require_role
from app.models.audit_log import AuditLog
from app.models.faculty import FacultyProfile
from app.services.scoring_service import update_faculty_profile_scores

router = APIRouter(prefix="/admin", tags=["Administration"])
logger = logging.getLogger(__name__)


@router.get("/audit-log", summary="Recent audit log entries")
async def get_audit_log(
    limit: int = Query(default=50, le=200),
    event_type: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_role("admin", "university")),
):
    """Returns recent audit log entries. Admin/University only."""
    query = select(AuditLog).order_by(desc(AuditLog.created_at)).limit(limit)
    if event_type:
        query = query.where(AuditLog.event_type == event_type)
    result = await db.execute(query)
    logs = result.scalars().all()
    return [
        {
            "event_id": log.event_id,
            "user_id": log.user_id,
            "user_role": log.user_role,
            "event_type": log.event_type,
            "event_outcome": log.event_outcome,
            "resource_type": log.resource_type,
            "ip_address": log.ip_address,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]


@router.post(
    "/scoring/recompute/{faculty_profile_id}",
    summary="Manually recompute scores for a faculty member",
)
async def recompute_scores(
    faculty_profile_id: str,
    term: str = Query(default="2025-S2"),
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_role("admin")),
):
    """Triggers a full statistical scoring recompute. Admin only."""
    result = await update_faculty_profile_scores(db, faculty_profile_id, term)
    if result is None:
        return {"message": "k-anonymity threshold not met or faculty not found"}
    return {
        "message": "Scores recomputed successfully",
        "composite_score": result.composite_score,
        "score_band": result.score_band,
        "response_count": result.response_count,
        "has_temporal_anomaly": result.has_temporal_anomaly,
    }


@router.post("/scoring/recompute-all", summary="Recompute scores for all faculties")
async def recompute_all_scores(
    term: str = Query(default="2025-S2"),
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_role("admin")),
):
    """Batch recompute scores for all faculty profiles. Admin only."""
    result = await db.execute(select(FacultyProfile))
    faculties = result.scalars().all()

    updated, skipped = 0, 0
    for faculty in faculties:
        scoring = await update_faculty_profile_scores(db, faculty.id, term)
        if scoring:
            updated += 1
        else:
            skipped += 1

    return {"updated": updated, "skipped_k_anonymity": skipped, "total": len(faculties)}


@router.get("/health", include_in_schema=True, summary="API health check")
async def health():
    """Basic liveness check."""
    return {"status": "ok"}
