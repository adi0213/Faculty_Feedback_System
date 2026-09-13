"""
Feedback ingestion service.
Handles: token generation, deduplication, spam pre-check, k-anonymity gate,
storage, and queuing NLP processing.
"""
import json
import logging
from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.exceptions import (
    FeedbackAlreadySubmittedError,
    KAnonymityNotMetError,
    NotFoundError,
)
from app.core.security import generate_pseudo_token, hash_pseudo_token
from app.models.faculty import FacultyProfile
from app.models.feedback import FeedbackRecord, SubmissionRecord
from app.models.token import PseudoToken
from app.schemas.feedback import FeedbackSubmitRequest, FeedbackSubmitResponse

logger = logging.getLogger(__name__)
settings = get_settings()


async def submit_feedback(
    db: AsyncSession,
    *,
    student_user_id: str,
    request: FeedbackSubmitRequest,
) -> FeedbackSubmitResponse:
    """
    Complete feedback submission pipeline:
    1. Validate faculty exists
    2. Generate pseudonymous token
    3. Check for duplicate submission
    4. Store feedback (anonymized)
    5. Queue NLP processing
    6. Return success response
    """
    # ── 1. Validate faculty exists ────────────────────────────────────────────
    result = await db.execute(
        select(FacultyProfile).where(FacultyProfile.id == request.faculty_profile_id)
    )
    faculty = result.scalar_one_or_none()
    if not faculty:
        raise NotFoundError("Faculty profile")

    # ── 2. Generate pseudonymous token ────────────────────────────────────────
    pseudo_token = generate_pseudo_token(
        student_user_id, request.faculty_profile_id, request.term
    )
    token_hash = hash_pseudo_token(pseudo_token)

    # ── 3. Check for duplicate ────────────────────────────────────────────────
    existing = await db.execute(
        select(SubmissionRecord).where(
            SubmissionRecord.student_token == token_hash,
            SubmissionRecord.faculty_profile_id == request.faculty_profile_id,
            SubmissionRecord.term == request.term,
        )
    )
    if existing.scalar_one_or_none():
        raise FeedbackAlreadySubmittedError()

    # ── 4. Store PseudoToken record in registry schema ────────────────────────
    pt = PseudoToken(
        user_id=student_user_id,
        faculty_profile_id=request.faculty_profile_id,
        term=request.term,
        token_hash=token_hash,
        is_used=True,
        used_at=datetime.now(timezone.utc),
    )
    db.add(pt)

    # ── 5. Record submission in deduplication table ───────────────────────────
    sub_record = SubmissionRecord(
        student_token=token_hash,
        faculty_profile_id=request.faculty_profile_id,
        term=request.term,
    )
    db.add(sub_record)

    # ── 6. Store anonymous feedback record ────────────────────────────────────
    feedback = FeedbackRecord(
        student_token=pseudo_token[:32],     # store first 32 chars (partial, for research correlation)
        faculty_profile_id=request.faculty_profile_id,
        term=request.term,
        scores_json=json.dumps(request.scores),
        comment_raw=request.comment,
        nlp_processed=False,
    )
    db.add(feedback)

    # ── 7. Update faculty response count (optimistic) ─────────────────────────
    faculty.response_count = (faculty.response_count or 0) + 1
    db.add(faculty)

    await db.flush()  # get IDs before queuing task

    # ── 8. Queue NLP processing task ──────────────────────────────────────────
    nlp_queued = False
    try:
        from app.tasks.worker import enqueue_nlp_task
        await enqueue_nlp_task(feedback.id)
        nlp_queued = True
    except Exception as e:
        logger.warning("Failed to enqueue NLP task for feedback %s: %s", feedback.id, e)
        # NLP will be processed in next batch — non-fatal

    logger.info(
        "feedback_submitted faculty=%s term=%s nlp_queued=%s",
        request.faculty_profile_id, request.term, nlp_queued
    )

    return FeedbackSubmitResponse(nlp_queued=nlp_queued)


async def check_submission_status(
    db: AsyncSession,
    *,
    student_user_id: str,
    faculty_profile_id: str,
    term: str,
) -> dict:
    """Check if a student has already submitted feedback for a faculty/term."""
    token_hash = hash_pseudo_token(
        generate_pseudo_token(student_user_id, faculty_profile_id, term)
    )
    result = await db.execute(
        select(SubmissionRecord).where(
            SubmissionRecord.student_token == token_hash,
            SubmissionRecord.faculty_profile_id == faculty_profile_id,
            SubmissionRecord.term == term,
        )
    )
    record = result.scalar_one_or_none()
    return {
        "submitted": record is not None,
        "term": term,
        "submitted_at": record.submitted_at if record else None,
    }


async def get_feedback_count(
    db: AsyncSession,
    faculty_profile_id: str,
    term: str,
) -> int:
    """Count non-spam feedback records for k-anonymity gate."""
    result = await db.execute(
        select(func.count(FeedbackRecord.id)).where(
            FeedbackRecord.faculty_profile_id == faculty_profile_id,
            FeedbackRecord.term == term,
            FeedbackRecord.is_spam == False,
        )
    )
    return result.scalar() or 0
