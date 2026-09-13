"""
Faculty development router — certificate uploads, course completions, score boost.
Endpoints:
  POST /faculty/courses/complete        — upload certificate + mark course complete
  GET  /faculty/courses/completed       — list all completions for logged-in faculty
  DELETE /faculty/courses/{completion_id} — remove a completion record
"""
import logging
import os
import shutil
import uuid
from pathlib import Path
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db, Base, engine
from app.dependencies import require_role
from app.models.faculty import FacultyProfile
from app.models.course_completion import CourseCompletion

router = APIRouter(prefix="/faculty/courses", tags=["Faculty Development"])
logger = logging.getLogger(__name__)

# Upload dir — prefer /tmp in containerised environments (read-only /app)
_PREFERRED_UPLOAD_DIR = Path(os.environ.get("UPLOAD_DIR", "uploads/certificates"))
_FALLBACK_UPLOAD_DIR  = Path("/tmp/edupulse/uploads/certificates")


def _get_upload_dir() -> Path:
    """Return a writable upload directory, falling back to /tmp on permission errors."""
    for candidate in (_PREFERRED_UPLOAD_DIR, _FALLBACK_UPLOAD_DIR):
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            return candidate
        except (PermissionError, OSError):
            continue
    raise RuntimeError("Cannot create upload directory in any writable location")


ALLOWED_TYPES = {"application/pdf", "image/jpeg", "image/png", "image/webp", "image/jpg"}
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".webp"}
MAX_SIZE_MB = 10
BOOST_PER_COURSE = 0.15
MAX_TOTAL_BOOST = 0.5


async def _ensure_tables():
    """Create course_completions table if it doesn't exist."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        logger.warning("Course completions schema initialization skipped: %s", e)


async def _get_faculty(db: AsyncSession, user_id: str) -> FacultyProfile:
    result = await db.execute(select(FacultyProfile).where(FacultyProfile.user_id == user_id))
    faculty = result.scalar_one_or_none()
    if not faculty:
        raise HTTPException(status_code=404, detail="Faculty profile not found")
    return faculty


@router.post("/complete", summary="Upload certificate and mark a course as completed")
async def complete_course(
    course_key: str = Form(..., description="Unique key, e.g. 'clarity_0'"),
    course_name: str = Form(...),
    provider: str = Form(..., description="Coursera | NPTEL | edX | MIT OCW | LinkedIn"),
    dimension_id: str = Form(..., description="clarity | methodology | punctuality | fairness | approachability | pacing | engagement"),
    certificate: UploadFile = File(..., description="PDF or image of the completion certificate"),
    db: AsyncSession = Depends(get_db),
    user=Depends(require_role("faculty")),
):
    """
    Faculty uploads a completion certificate for a recommended course.
    Each completion grants a +0.15 score boost (capped at +0.5 total).
    """
    # ── Validate file type & size ────────────────────────────────────────────
    ext = Path(certificate.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    content = await certificate.read()
    if len(content) > MAX_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File exceeds {MAX_SIZE_MB}MB limit")

    faculty = await _get_faculty(db, user.id)

    # ── Prevent duplicate completions for same course ────────────────────────
    existing = await db.execute(
        select(CourseCompletion).where(
            CourseCompletion.faculty_profile_id == faculty.id,
            CourseCompletion.course_key == course_key,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Course already marked as completed")

    # ── Cap total boost ──────────────────────────────────────────────────────
    total_res = await db.execute(
        select(func.sum(CourseCompletion.score_boost)).where(
            CourseCompletion.faculty_profile_id == faculty.id
        )
    )
    current_boost = float(total_res.scalar() or 0.0)
    if current_boost >= MAX_TOTAL_BOOST:
        boost = 0.0  # Already at cap — still mark as complete
    else:
        boost = min(BOOST_PER_COURSE, MAX_TOTAL_BOOST - current_boost)

    # ── Save file ────────────────────────────────────────────────────────────
    upload_dir = _get_upload_dir()
    unique_name = f"{faculty.id}_{uuid.uuid4().hex}{ext}"
    dest = upload_dir / unique_name
    with open(dest, "wb") as f:
        f.write(content)

    cert_url = f"/uploads/certificates/{unique_name}"

    # ── Persist completion record ────────────────────────────────────────────
    completion = CourseCompletion(
        faculty_profile_id=faculty.id,
        course_key=course_key,
        course_name=course_name,
        provider=provider,
        dimension_id=dimension_id,
        certificate_filename=unique_name,
        certificate_url=cert_url,
        score_boost=boost,
        completed_at=datetime.now(timezone.utc),
    )
    db.add(completion)
    await db.flush()

    logger.info(
        "Faculty %s completed course '%s' (boost=%.2f, total_boost=%.2f)",
        faculty.faculty_code, course_name, boost, current_boost + boost
    )

    return {
        "id": completion.id,
        "course_key": course_key,
        "course_name": course_name,
        "provider": provider,
        "dimension_id": dimension_id,
        "certificate_url": cert_url,
        "score_boost": boost,
        "total_boost_earned": round(float(current_boost + boost), 2),
        "max_boost": MAX_TOTAL_BOOST,
        "completed_at": completion.completed_at.isoformat(),
    }


@router.get("/completed", summary="List all completed courses for the logged-in faculty")
async def list_completed_courses(
    db: AsyncSession = Depends(get_db),
    user=Depends(require_role("faculty")),
):
    """Returns all course completions for the logged-in faculty with total boost."""
    faculty = await _get_faculty(db, user.id)

    result = await db.execute(
        select(CourseCompletion)
        .where(CourseCompletion.faculty_profile_id == faculty.id)
        .order_by(CourseCompletion.completed_at.desc())
    )
    completions = result.scalars().all()

    total_boost = round(float(sum(float(c.score_boost) for c in completions)), 2) if completions else 0.0

    return {
        "faculty_id": faculty.id,
        "total_boost": total_boost,
        "max_boost": MAX_TOTAL_BOOST,
        "completed_count": len(completions),
        "completions": [
            {
                "id": c.id,
                "course_key": c.course_key,
                "course_name": c.course_name,
                "provider": c.provider,
                "dimension_id": c.dimension_id,
                "certificate_url": c.certificate_url,
                "score_boost": c.score_boost,
                "completed_at": c.completed_at.isoformat() if c.completed_at else None,
            }
            for c in completions
        ],
    }


@router.delete("/{completion_id}", summary="Remove a course completion record")
async def delete_completion(
    completion_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_role("faculty")),
):
    """Allows a faculty to remove an incorrectly uploaded completion."""
    faculty = await _get_faculty(db, user.id)

    result = await db.execute(
        select(CourseCompletion).where(
            CourseCompletion.id == completion_id,
            CourseCompletion.faculty_profile_id == faculty.id,
        )
    )
    completion = result.scalar_one_or_none()
    if not completion:
        raise HTTPException(status_code=404, detail="Completion record not found")

    # Remove file from disk
    if completion.certificate_filename:
        upload_dir = _get_upload_dir()
        path = upload_dir / completion.certificate_filename
        if path.exists():
            path.unlink()

    await db.delete(completion)
    return {"deleted": completion_id}
