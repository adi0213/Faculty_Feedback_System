"""Feedback router — submit, check status, admin list."""
import logging
from fastapi import APIRouter, Depends, Request

from app.core.audit import audit_context_from_request, log_event
from app.core.rate_limit import feedback_rate_limit
from app.db.session import get_db
from app.dependencies import require_role
from app.schemas.feedback import FeedbackStatusResponse, FeedbackSubmitRequest, FeedbackSubmitResponse
from app.services import feedback_service

router = APIRouter(prefix="/feedback", tags=["Feedback"])
logger = logging.getLogger(__name__)


@router.post(
    "/submit",
    response_model=FeedbackSubmitResponse,
    summary="Submit anonymous faculty feedback",
)
async def submit_feedback(
    req: FeedbackSubmitRequest,
    request: Request,
    db=Depends(get_db),
    user=Depends(require_role("student")),
    _rl=Depends(feedback_rate_limit),
):
    """
    Submit feedback for a faculty member. Requires student role.
    - One submission allowed per (student, faculty, term).
    - Comment is sanitized server-side.
    - Submission is anonymized via HMAC token before storage.
    - NLP processing queued asynchronously.
    """
    ctx = audit_context_from_request(request)
    result = await feedback_service.submit_feedback(
        db, student_user_id=user.id, request=req
    )
    await log_event(
        db, event_type="feedback.submit", event_outcome="success",
        user_id=user.id, user_role=user.role,
        resource_type="feedback", **ctx,
        details={"faculty_profile_id": req.faculty_profile_id, "term": req.term},
    )
    return result


@router.get(
    "/status",
    response_model=FeedbackStatusResponse,
    summary="Check if student has submitted feedback for a faculty",
)
async def check_status(
    faculty_profile_id: str,
    term: str,
    db=Depends(get_db),
    user=Depends(require_role("student")),
):
    """
    Returns whether the current student has already submitted feedback
    for the given faculty/term combination.
    """
    status = await feedback_service.check_submission_status(
        db,
        student_user_id=user.id,
        faculty_profile_id=faculty_profile_id,
        term=term,
    )
    return FeedbackStatusResponse(**status)
