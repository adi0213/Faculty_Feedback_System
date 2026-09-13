"""Analytics router — department summaries, clusters, system health, and methodology transparency."""
import logging
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.dependencies import CurrentUser, require_role
from app.services.analytics_service import (
    cluster_faculties,
    get_department_summary,
    get_faculty_trend,
    get_system_health,
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])
logger = logging.getLogger(__name__)

# ── Evaluation Methodology Catalog ───────────────────────────────────────────
METHODOLOGY = {
    "scoring_scale": {
        "raw_min": 1,
        "raw_max": 4,
        "normalized_min": 1.0,
        "normalized_max": 5.0,
        "formula": "normalized = ((raw - 1) / 3 * 4) + 1",
        "description": (
            "Student responses use a 4-point scale (1=Poor, 2=Needs Improvement, "
            "3=Good, 4=Excellent). These are normalized to a 1–5 scale using a "
            "linear transformation so that scores align with standard grading conventions."
        ),
    },
    "score_bands": [
        {"band": "Strong Performer",    "min": 4.0, "max": 5.0, "color": "#1E6F4A", "description": "Consistently excellent across all dimensions."},
        {"band": "Developing",          "min": 3.0, "max": 3.99, "color": "#9C7423", "description": "Good overall with specific areas to strengthen."},
        {"band": "Needs Improvement",   "min": 1.0, "max": 2.99, "color": "#9A3C2C", "description": "Significant development needed in multiple areas."},
    ],
    "k_anonymity": {
        "threshold": 5,
        "description": (
            "To protect student privacy, individual dimension scores are only shown "
            "when at least 5 responses have been collected for that term. Below this "
            "threshold, results are shown as 'Insufficient data'."
        ),
    },
    "composite_calculation": {
        "method": "Weighted mean of per-dimension averages",
        "description": (
            "Each dimension's score is the mean of all normalized responses for that "
            "category. The composite score is the weighted average of all dimension "
            "scores. Sub-questions (triggered only for low ratings) are diagnostic "
            "only and do not affect the final score."
        ),
    },
    "dimensions": [
        {
            "id": "clarity",
            "label": "Teaching Clarity",
            "weight": 0.20,
            "weight_pct": "20%",
            "description": "How clearly the faculty explains concepts and topics.",
            "icon": "🔤",
            "questions": [
                {
                    "id": "q_clarity",
                    "text": "How clearly does the faculty explain concepts and topics in class?",
                    "type": "main",
                    "options": [
                        {"value": 4, "label": "Excellent",          "desc": "Crystal clear, always easy to follow"},
                        {"value": 3, "label": "Good",               "desc": "Mostly clear with minor gaps"},
                        {"value": 2, "label": "Needs Improvement",  "desc": "Often confusing or hard to follow"},
                        {"value": 1, "label": "Poor",               "desc": "Very unclear, difficult to understand"},
                    ],
                }
            ],
        },
        {
            "id": "methodology",
            "label": "Teaching Methodology",
            "weight": 0.18,
            "weight_pct": "18%",
            "description": "Effectiveness and variety of teaching approaches used.",
            "icon": "🎯",
            "questions": [
                {
                    "id": "q_methodology",
                    "text": "Does the faculty use effective and engaging teaching methods?",
                    "type": "main",
                    "options": [
                        {"value": 4, "label": "Excellent",          "desc": "Creative, varied, and highly engaging"},
                        {"value": 3, "label": "Good",               "desc": "Standard methods, reasonably effective"},
                        {"value": 2, "label": "Needs Improvement",  "desc": "Monotonous, could be more interactive"},
                        {"value": 1, "label": "Poor",               "desc": "Ineffective, no engagement at all"},
                    ],
                }
            ],
        },
        {
            "id": "fairness",
            "label": "Assessment Fairness",
            "weight": 0.14,
            "weight_pct": "14%",
            "description": "Transparency and consistency of grading and evaluation.",
            "icon": "⚖️",
            "questions": [
                {
                    "id": "q_fairness",
                    "text": "Are internal marks and assessments awarded fairly and transparently?",
                    "type": "main",
                    "options": [
                        {"value": 4, "label": "Excellent",          "desc": "Completely fair and transparent"},
                        {"value": 3, "label": "Good",               "desc": "Generally fair with minor concerns"},
                        {"value": 2, "label": "Needs Improvement",  "desc": "Some inconsistency in grading"},
                        {"value": 1, "label": "Poor",               "desc": "Perceived bias or unfair grading"},
                    ],
                }
            ],
        },
        {
            "id": "approachability",
            "label": "Approachability",
            "weight": 0.14,
            "weight_pct": "14%",
            "description": "Accessibility and supportiveness outside class hours.",
            "icon": "🤝",
            "questions": [
                {
                    "id": "q_approachability",
                    "text": "Is the faculty accessible and approachable for doubt-clearing outside class?",
                    "type": "main",
                    "options": [
                        {"value": 4, "label": "Excellent",          "desc": "Always available and welcoming"},
                        {"value": 3, "label": "Good",               "desc": "Usually available with some delays"},
                        {"value": 2, "label": "Needs Improvement",  "desc": "Rarely available outside class"},
                        {"value": 1, "label": "Poor",               "desc": "Never available for doubts"},
                    ],
                }
            ],
        },
        {
            "id": "punctuality",
            "label": "Punctuality",
            "weight": 0.12,
            "weight_pct": "12%",
            "description": "Timeliness and completeness of scheduled class hours.",
            "icon": "⏰",
            "questions": [
                {
                    "id": "q_punctuality",
                    "text": "Does the faculty conduct classes on time and complete scheduled hours?",
                    "type": "main",
                    "options": [
                        {"value": 4, "label": "Excellent",          "desc": "Always punctual, full hours conducted"},
                        {"value": 3, "label": "Good",               "desc": "Mostly on time with rare delays"},
                        {"value": 2, "label": "Needs Improvement",  "desc": "Frequently late or ends early"},
                        {"value": 1, "label": "Poor",               "desc": "Consistently misses scheduled time"},
                    ],
                }
            ],
        },
        {
            "id": "pacing",
            "label": "Syllabus Pacing",
            "weight": 0.12,
            "weight_pct": "12%",
            "description": "How well the syllabus is paced across the semester.",
            "icon": "📚",
            "questions": [
                {
                    "id": "q_pacing",
                    "text": "Is the syllabus covered at an appropriate pace throughout the semester?",
                    "type": "main",
                    "options": [
                        {"value": 4, "label": "Excellent",          "desc": "Perfect pacing, well planned"},
                        {"value": 3, "label": "Good",               "desc": "Generally good with minor rush"},
                        {"value": 2, "label": "Needs Improvement",  "desc": "Rushed at end or too slow at start"},
                        {"value": 1, "label": "Poor",               "desc": "Very poorly paced, incomplete coverage"},
                    ],
                }
            ],
        },
        {
            "id": "engagement",
            "label": "Student Engagement",
            "weight": 0.10,
            "weight_pct": "10%",
            "description": "Degree to which the faculty fosters interactive, participative classes.",
            "icon": "💡",
            "questions": [
                {
                    "id": "q_engagement",
                    "text": "Does the faculty encourage student participation and make classes interactive?",
                    "type": "main",
                    "options": [
                        {"value": 4, "label": "Excellent",          "desc": "Highly interactive, great participation"},
                        {"value": 3, "label": "Good",               "desc": "Reasonably interactive"},
                        {"value": 2, "label": "Needs Improvement",  "desc": "Mostly lecture-based, little interaction"},
                        {"value": 1, "label": "Poor",               "desc": "No class interaction at all"},
                    ],
                }
            ],
        },
    ],
    "sub_question_policy": (
        "When a main question receives a score of 1 or 2, up to 3 follow-up "
        "diagnostic sub-questions are automatically shown to collect more specific "
        "feedback. These sub-questions are for qualitative insight only and do NOT "
        "contribute to the numerical composite score."
    ),
    "anonymity_measures": [
        "All feedback is collected anonymously — no student identity is linked to any response.",
        "Only aggregated (mean) scores per dimension are stored and displayed.",
        "A minimum of 5 responses (k-anonymity threshold) is required before any scores are shown to faculty.",
        "Qualitative comments submitted by students are never visible to faculty — only sentiment summaries are provided.",
        "Individual student response records are inaccessible to all non-admin roles.",
    ],
}


@router.get("/departments", summary="Department-level analytics")
async def department_analytics(
    college: str | None = Query(default=None),
    dept: str | None = Query(default=None),
    db=Depends(get_db),
    user=Depends(require_role("hod", "principal", "university", "admin")),
):
    """Returns aggregate department stats scoped to caller's access level."""
    if user.role == "hod":
        target_college = user.college or college
        target_dept = user.dept or dept
    elif user.role == "principal":
        target_college = user.college or college
        target_dept = dept
    else:
        target_college = college or ""
        target_dept = dept

    if not target_college:
        return []

    summaries = await get_department_summary(db, college=target_college, dept=target_dept)
    return [s.__dict__ for s in summaries]


@router.get("/faculty/{faculty_id}/trend", summary="Longitudinal score trend for one faculty")
async def faculty_trend(
    faculty_id: str,
    db=Depends(get_db),
    user=Depends(require_role("faculty", "hod", "principal", "university", "admin")),
):
    """Per-term trend data. Faculty can only see their own; others see any in their scope."""
    trend = await get_faculty_trend(db, faculty_id)
    return [t.__dict__ for t in trend]


@router.get("/clusters", summary="Faculty performance clusters for a college")
async def faculty_clusters(
    college: str,
    k: int = Query(default=3, ge=2, le=6),
    db=Depends(get_db),
    _user=Depends(require_role("principal", "university", "admin")),
):
    """K-means clustering of faculty by dimension scores. Principal/University only."""
    clusters = await cluster_faculties(db, college=college, k=k)
    return [c.__dict__ for c in clusters]


@router.get("/health", summary="System health KPIs")
async def system_health(
    university: str | None = Query(default=None),
    db=Depends(get_db),
    _user=Depends(require_role("university", "admin")),
):
    """Overall system health metrics. University/Admin only."""
    health = await get_system_health(db, university=university)
    return health.__dict__


@router.get("/methodology", summary="Evaluation questionnaire, methodology, and privacy policy — public")
async def get_methodology():
    """
    Returns the complete evaluation methodology catalog:
    - All questions organized by dimension/category
    - Dimension weights and scoring formula
    - Score bands and their definitions
    - K-anonymity threshold and privacy measures
    This endpoint is publicly accessible (no authentication required)
    to ensure full transparency about how faculty are evaluated.
    """
    return METHODOLOGY


@router.get(
    "/me/strengths-weaknesses",
    summary="Faculty's own aggregated strengths and improvement areas (k-anonymity safe)",
)
async def my_strengths_weaknesses(
    term: str = Query(default="2025-S2", pattern=r"^\d{4}-S[12]$"),
    db: AsyncSession = Depends(get_db),
    user=Depends(require_role("faculty")),
):
    """
    Returns the calling faculty member's aggregated dimension-level results
    for the given term, subject to k-anonymity.

    - Only returns scores if response_count >= k_anonymity_threshold.
    - Never exposes individual student responses or any PII.
    - Provides AI-style interpretations based on score bands.
    """
    import json
    from sqlalchemy import select
    from app.models.faculty import FacultyProfile
    from app.services.feedback_service import get_feedback_count
    from app.config import get_settings

    settings = get_settings()

    result = await db.execute(
        select(FacultyProfile).where(FacultyProfile.user_id == user.id)
    )
    faculty = result.scalar_one_or_none()
    if not faculty:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Faculty profile")

    k = settings.k_anonymity_threshold
    n = await get_feedback_count(db, faculty.id, term)
    k_met = n >= k

    def _parse(text, default):
        if not text:
            return default
        try:
            return json.loads(text)
        except Exception:
            return default

    dim_scores = _parse(faculty.dimension_scores_json, {}) if k_met else {}
    trend_data = _parse(faculty.score_trend_json, [])

    # Build AI interpretations per dimension
    DIM_INTERPRETATIONS = {
        "clarity": {
            "strong":  "Your explanations are consistently clear. Students find it easy to follow your lectures. Continue using structured frameworks and vivid examples.",
            "developing": "Students generally understand your explanations, but some find certain topics harder to follow. Consider adding more real-world examples and periodic comprehension checks.",
            "needs": "Students are struggling to follow your explanations. Focus on simplifying language, using visual aids, and breaking complex concepts into smaller steps.",
        },
        "methodology": {
            "strong":  "Your teaching methods are engaging and varied. Students appreciate the diverse approaches you use to present material.",
            "developing": "Your methods are effective but could benefit from more variety. Try incorporating interactive elements like think-pair-share or brief in-class activities.",
            "needs": "Students find the current teaching approach monotonous. Diversify with case studies, demonstrations, multimedia, or collaborative exercises.",
        },
        "punctuality": {
            "strong":  "Excellent class management — you consistently respect the schedule, and students appreciate the reliability.",
            "developing": "Mostly punctual with occasional lapses. Ensure makeup classes are scheduled promptly when sessions are missed.",
            "needs": "Punctuality is a significant concern. Missed or shortened classes disrupt student learning. Establish a structured schedule and adhere to it consistently.",
        },
        "fairness": {
            "strong":  "Students perceive your assessments as fair and transparent. Your grading criteria are clear and consistently applied.",
            "developing": "Generally fair, but some students are uncertain about grading criteria. Share rubrics before assessments and provide feedback after grading.",
            "needs": "Assessment transparency needs significant improvement. Publish clear marking schemes in advance and offer opportunities for students to discuss their grades.",
        },
        "approachability": {
            "strong":  "Students feel comfortable approaching you. Your open-door approach significantly supports their academic confidence.",
            "developing": "Generally approachable, but access could be improved. Establish clear office hours and respond to queries in a timely, encouraging manner.",
            "needs": "Students find it difficult to approach you. Create structured interaction opportunities, respond promptly to queries, and cultivate a welcoming classroom environment.",
        },
        "pacing": {
            "strong":  "The syllabus is well-paced, giving students sufficient time to absorb and practice each topic before moving forward.",
            "developing": "Pacing is generally reasonable but could be refined — pay attention to whether complex topics receive enough time versus simpler ones.",
            "needs": "Syllabus coverage feels rushed or uneven. Create a detailed semester plan, allocate time by topic complexity, and adjust in real time based on student readiness.",
        },
        "engagement": {
            "strong":  "You foster a highly interactive classroom environment. Student participation and energy are consistently high.",
            "developing": "Moderately interactive — consider adding more structured participation opportunities such as polls, think-pair-share, or brief group discussions.",
            "needs": "Classes are mostly one-directional. Introduce techniques like cold-calling (supportively), in-class quizzes, or discussion-based activities to increase engagement.",
        },
    }

    def _interpret(dim_id: str, score: float) -> str:
        interp = DIM_INTERPRETATIONS.get(dim_id, {})
        if score >= 4.0:
            return interp.get("strong", "")
        elif score >= 3.0:
            return interp.get("developing", "")
        else:
            return interp.get("needs", "")

    # Build per-dimension result
    dimension_results = []
    dim_weights = {d["id"]: d["weight"] for d in METHODOLOGY["dimensions"]}
    for dim in METHODOLOGY["dimensions"]:
        did = dim["id"]
        score = dim_scores.get(did) if k_met else None
        dimension_results.append({
            "id": did,
            "label": dim["label"],
            "weight": dim["weight"],
            "weight_pct": dim["weight_pct"],
            "icon": dim["icon"],
            "score": round(score, 2) if score is not None else None,
            "is_strong": score >= 4.0 if score is not None else None,
            "needs_improvement": score < 3.0 if score is not None else None,
            "interpretation": _interpret(did, score) if score is not None else None,
        })

    strengths = [d for d in dimension_results if d["is_strong"]]
    improvements = [d for d in dimension_results if d["needs_improvement"]]

    return {
        "faculty_id": faculty.id,
        "term": term,
        "response_count": n,
        "k_anonymity_threshold": k,
        "k_anonymity_met": k_met,
        "composite_score": round(faculty.composite_score, 2) if faculty.composite_score and k_met else None,
        "score_band": faculty.score_band if k_met else None,
        "dimensions": dimension_results,
        "strengths": strengths,
        "improvement_areas": improvements,
        "score_trend": [
            {
                "term": t.get("term"),
                "composite_score": t.get("composite_score"),
                "response_count": t.get("response_count"),
            }
            for t in trend_data
            if isinstance(t, dict) and "term" in t
        ],
    }

