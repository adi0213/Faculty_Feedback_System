"""
Recommendation service — orchestrates RAG retrieval + LLM generation.
Produces evidence-based course recommendations and roadmaps.
"""
import json
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm_client import generate_recommendations, generate_roadmap
from app.ai.rag_engine import get_rag_engine
from app.ai.topic_extractor import extract_corpus_topics
from app.config import get_settings
from app.core.exceptions import KAnonymityNotMetError, NotFoundError
from app.models.course_catalog import CourseCatalogEntry
from app.models.faculty import FacultyProfile
from app.models.feedback import FeedbackRecord
from app.models.roadmap import CourseRecommendation, FacultyRoadmap
from app.services.scoring_service import SCORE_DIMENSIONS

logger = logging.getLogger(__name__)
settings = get_settings()


def _identify_weak_dimensions(display_scores: dict[str, float], threshold: float = 3.0) -> list[str]:
    """Return dimensions with average score below threshold, ranked worst-first."""
    weak = [(dim, score) for dim, score in display_scores.items() if score < threshold]
    return [dim for dim, _ in sorted(weak, key=lambda x: x[1])]


def _identify_strong_dimensions(display_scores: dict[str, float], threshold: float = 4.0) -> list[str]:
    return [dim for dim, score in display_scores.items() if score >= threshold]


async def generate_faculty_recommendations(
    db: AsyncSession,
    faculty_profile_id: str,
    term: str,
) -> list[CourseRecommendation]:
    """
    Full pipeline: load scores → RAG retrieval → LLM generation → persist.
    Returns list of CourseRecommendation records.
    """
    # ── Load faculty profile ──────────────────────────────────────────────────
    fac_result = await db.execute(
        select(FacultyProfile).where(FacultyProfile.id == faculty_profile_id)
    )
    faculty = fac_result.scalar_one_or_none()
    if not faculty:
        raise NotFoundError("Faculty profile")

    n = faculty.response_count or 0
    if n < settings.k_anonymity_threshold:
        raise KAnonymityNotMetError(current=n, required=settings.k_anonymity_threshold)

    # ── Parse dimension scores ────────────────────────────────────────────────
    try:
        display_scores: dict[str, float] = json.loads(faculty.dimension_scores_json or "{}")
    except (json.JSONDecodeError, TypeError):
        display_scores = {}

    weak_dims = _identify_weak_dimensions(display_scores)
    if not weak_dims:
        weak_dims = list(display_scores.keys())[:2]  # Take bottom 2 if all good

    # ── Extract feedback themes via NLP corpus ────────────────────────────────
    fb_result = await db.execute(
        select(FeedbackRecord.comment_raw, FeedbackRecord.topics_json).where(
            FeedbackRecord.faculty_profile_id == faculty_profile_id,
            FeedbackRecord.term == term,
            FeedbackRecord.is_spam.is_(False),
            FeedbackRecord.comment_raw.isnot(None),
        )
    )
    fb_rows = fb_result.fetchall()
    comments = [row.comment_raw for row in fb_rows if row.comment_raw]
    feedback_themes = extract_corpus_topics(comments, max_topics=5)

    # Also collect topics from NLP-processed records
    for row in fb_rows:
        if row.topics_json:
            try:
                topics = json.loads(row.topics_json)
                for t in topics:
                    if t not in feedback_themes:
                        feedback_themes.append(t)
            except (json.JSONDecodeError, TypeError):
                pass

    # ── RAG: Retrieve relevant courses ───────────────────────────────────────
    rag = get_rag_engine()
    query = f"faculty development {' '.join(weak_dims)} teaching improvement {faculty.dept}"
    retrieved = rag.retrieve(
        query=query,
        target_dimensions=weak_dims,
        top_k=6,
    )

    retrieved_dicts = [
        {
            "title": c.title,
            "provider": c.provider,
            "duration_label": c.duration_label,
            "description": c.description,
            "primary_dimension": c.primary_dimension,
        }
        for c in retrieved
    ]

    # ── LLM: Generate recommendations ────────────────────────────────────────
    llm_response = await generate_recommendations(
        dept=faculty.dept,
        subject=faculty.subject or faculty.dept,
        score_band=faculty.score_band or "developing",
        composite_score=faculty.composite_score or 3.0,
        response_count=n,
        weak_dimensions=weak_dims,
        feedback_themes=feedback_themes[:8],
        retrieved_courses=retrieved_dicts,
    )

    # ── Persist recommendations ───────────────────────────────────────────────
    recs: list[CourseRecommendation] = []
    llm_recs = llm_response.parsed_json.get("recommendations", [])

    for llm_rec in llm_recs[:6]:
        # Match LLM course title to retrieved RAG result for DB linking
        matched_course_id = None
        for c in retrieved:
            if c.title.lower() in llm_rec.get("course_title", "").lower():
                matched_course_id = c.course_id if not c.course_id.startswith("catalog_") else None
                break

        evidence = [
            {
                "source": "absa",
                "dimension": llm_rec.get("target_dimension", ""),
                "description": f"Feedback analysis identified '{llm_rec.get('target_dimension', '')}' as a weak area",
                "weight": llm_rec.get("confidence_score", 0.7),
            }
        ]
        for theme in feedback_themes[:3]:
            evidence.append({
                "source": "topic_model",
                "dimension": llm_rec.get("target_dimension", ""),
                "description": f"Recurring feedback theme: '{theme}'",
                "weight": 0.6,
            })

        rec = CourseRecommendation(
            faculty_profile_id=faculty_profile_id,
            course_id=matched_course_id,
            term=term,
            target_dimension=llm_rec.get("target_dimension", weak_dims[0] if weak_dims else "overall"),
            evidence_json=json.dumps(evidence),
            confidence_score=float(llm_rec.get("confidence_score", 0.75)),
            justification_text=llm_rec.get("justification", ""),
            learning_outcomes_text=llm_rec.get("learning_outcomes_summary", ""),
            expected_impact_text=llm_rec.get("expected_impact", ""),
        )
        db.add(rec)
        recs.append(rec)

    await db.flush()
    logger.info("Generated %d recommendations for faculty %s", len(recs), faculty_profile_id)
    return recs


async def generate_faculty_roadmap(
    db: AsyncSession,
    faculty_profile_id: str,
    faculty_user_id: str,
    term: str,
) -> FacultyRoadmap:
    """Generate and persist a 30/60/90-day roadmap for a faculty member."""
    fac_result = await db.execute(
        select(FacultyProfile).where(FacultyProfile.id == faculty_profile_id)
    )
    faculty = fac_result.scalar_one_or_none()
    if not faculty:
        raise NotFoundError("Faculty profile")

    try:
        display_scores: dict = json.loads(faculty.dimension_scores_json or "{}")
    except (json.JSONDecodeError, TypeError):
        display_scores = {}

    weak_dims = _identify_weak_dimensions(display_scores)[:3]

    # Get existing recommendation titles
    rec_result = await db.execute(
        select(CourseRecommendation).where(
            CourseRecommendation.faculty_profile_id == faculty_profile_id,
            CourseRecommendation.term == term,
        )
    )
    recs = rec_result.scalars().all()
    course_titles = [
        r.justification_text[:50] if r.justification_text else "Recommended course"
        for r in recs[:3]
    ]

    llm_response = await generate_roadmap(
        dept=faculty.dept,
        score_band=faculty.score_band or "developing",
        composite_score=faculty.composite_score or 3.0,
        weak_dimensions=weak_dims,
        recommended_courses=course_titles,
    )

    roadmap_data = llm_response.parsed_json
    exec_summary = roadmap_data.pop("executive_summary", None)
    root_cause = roadmap_data.pop("root_cause_analysis", None)

    roadmap = FacultyRoadmap(
        faculty_profile_id=faculty_profile_id,
        faculty_id=faculty_user_id,
        term=term,
        score_band=faculty.score_band or "developing",
        composite_score=faculty.composite_score or 3.0,
        day30_plan_json=json.dumps(roadmap_data.get("day30", {})),
        day60_plan_json=json.dumps(roadmap_data.get("day60", {})),
        day90_plan_json=json.dumps(roadmap_data.get("day90", {})),
        executive_summary=exec_summary,
        root_cause_analysis=root_cause,
        is_published=False,
    )
    db.add(roadmap)
    await db.flush()
    logger.info("Generated roadmap for faculty %s term %s", faculty_profile_id, term)
    return roadmap
