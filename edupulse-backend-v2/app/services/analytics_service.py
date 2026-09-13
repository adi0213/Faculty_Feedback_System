"""
Analytics service — longitudinal trends, clustering, regression, and system health KPIs.
Feeds the HoD, Principal, and University dashboards.
"""
import json
import logging
import math
import statistics
from collections import defaultdict
from dataclasses import dataclass, field

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.faculty import FacultyProfile
from app.models.feedback import FeedbackRecord, SubmissionRecord

logger = logging.getLogger(__name__)


# ── Data classes for analytics responses ─────────────────────────────────────

@dataclass
class DepartmentSummary:
    dept: str
    college: str
    faculty_count: int
    avg_composite: float | None
    strong_count: int
    developing_count: int
    needs_support_count: int
    response_count: int
    participation_rate: float | None   # 0.0–1.0
    flagged_count: int


@dataclass
class TrendPoint:
    term: str
    composite_score: float
    response_count: int
    score_band: str


@dataclass
class DimensionRanking:
    dimension: str
    dept_avg: float
    college_avg: float
    trend: str  # "improving" | "stable" | "declining"


@dataclass
class FacultyCluster:
    cluster_id: int
    label: str      # e.g. "Content-Strong, Engagement-Weak"
    faculty_ids: list[str]
    centroid: dict[str, float]


@dataclass
class SystemHealthKPI:
    total_faculties: int
    total_feedback_submissions: int
    avg_composite_score: float | None
    participation_rate: float
    faculties_with_reports: int
    faculties_flagged: int
    nlp_processed_rate: float
    strong_pct: float
    developing_pct: float
    needs_support_pct: float


# ── Helper functions ──────────────────────────────────────────────────────────

def _safe_mean(vals: list[float]) -> float | None:
    return statistics.mean(vals) if vals else None


def _band_counts(faculties: list[FacultyProfile]) -> tuple[int, int, int]:
    strong = sum(1 for f in faculties if f.score_band == "strong")
    developing = sum(1 for f in faculties if f.score_band == "developing")
    needs = sum(1 for f in faculties if f.score_band == "needs_support")
    return strong, developing, needs


# ── Department-level analytics ────────────────────────────────────────────────

async def get_department_summary(
    db: AsyncSession,
    college: str,
    dept: str | None = None,
) -> list[DepartmentSummary]:
    """Aggregate per-department stats for HoD / Principal dashboards."""
    query = select(FacultyProfile).where(FacultyProfile.college == college)
    if dept:
        query = query.where(FacultyProfile.dept == dept)

    result = await db.execute(query)
    all_faculties = result.scalars().all()

    # Group by department
    by_dept: dict[str, list[FacultyProfile]] = defaultdict(list)
    for f in all_faculties:
        by_dept[f.dept].append(f)

    summaries = []
    for dept_name, faculties in by_dept.items():
        composites = [f.composite_score for f in faculties if f.composite_score is not None]
        strong, developing, needs = _band_counts(faculties)
        total_responses = sum(f.response_count for f in faculties)
        flagged = sum(1 for f in faculties if f.has_anomaly_flag)

        summaries.append(DepartmentSummary(
            dept=dept_name,
            college=college,
            faculty_count=len(faculties),
            avg_composite=round(_safe_mean(composites), 2) if composites else None,
            strong_count=strong,
            developing_count=developing,
            needs_support_count=needs,
            response_count=total_responses,
            participation_rate=None,  # Would need enrolled count from registry
            flagged_count=flagged,
        ))

    return sorted(summaries, key=lambda x: x.avg_composite or 0, reverse=True)


# ── Longitudinal trend analysis ───────────────────────────────────────────────

async def get_faculty_trend(
    db: AsyncSession,
    faculty_profile_id: str,
) -> list[TrendPoint]:
    """Return per-term trend data for a single faculty member."""
    result = await db.execute(
        select(FacultyProfile).where(FacultyProfile.id == faculty_profile_id)
    )
    faculty = result.scalar_one_or_none()
    if not faculty or not faculty.score_trend_json:
        return []

    try:
        trend_data = json.loads(faculty.score_trend_json)
    except (json.JSONDecodeError, TypeError):
        return []

    return [
        TrendPoint(
            term=t.get("term", ""),
            composite_score=t.get("composite_score", 0.0),
            response_count=t.get("response_count", 0),
            score_band=t.get("score_band", "developing"),
        )
        for t in sorted(trend_data, key=lambda x: x.get("term", ""))
    ]


# ── K-means clustering ────────────────────────────────────────────────────────

def _euclidean(a: dict[str, float], b: dict[str, float], dims: list[str]) -> float:
    return math.sqrt(sum((a.get(d, 0) - b.get(d, 0)) ** 2 for d in dims))


def _cluster_label(centroid: dict[str, float]) -> str:
    """Generate a human-readable label from a cluster centroid."""
    dims_sorted = sorted(centroid.items(), key=lambda x: x[1])
    weak = dims_sorted[0][0] if dims_sorted else "unknown"
    strong = dims_sorted[-1][0] if dims_sorted else "unknown"
    return f"{strong.capitalize()}-Strong, {weak.capitalize()}-Weak"


async def cluster_faculties(
    db: AsyncSession,
    college: str,
    k: int = 3,
) -> list[FacultyCluster]:
    """
    Simple k-means clustering over dimension scores for faculties in a college.
    Returns k clusters with centroid and member IDs.
    """
    result = await db.execute(
        select(FacultyProfile).where(
            FacultyProfile.college == college,
            FacultyProfile.dimension_scores_json.isnot(None),
            FacultyProfile.composite_score.isnot(None),
        )
    )
    faculties = result.scalars().all()
    if len(faculties) < k:
        return []

    # Parse scores
    faculty_vecs: list[tuple[str, dict[str, float]]] = []
    for f in faculties:
        try:
            scores = json.loads(f.dimension_scores_json)
            if scores:
                faculty_vecs.append((f.id, scores))
        except (json.JSONDecodeError, TypeError):
            pass

    if not faculty_vecs:
        return []

    dims = list(faculty_vecs[0][1].keys())
    n = len(faculty_vecs)
    k = min(k, n)

    # Initialize centroids from evenly-spaced members
    step = max(1, n // k)
    centroids = [dict(faculty_vecs[i * step][1]) for i in range(k)]

    # Iterate k-means
    for _ in range(10):
        clusters: dict[int, list[tuple[str, dict]]] = defaultdict(list)
        for fid, vec in faculty_vecs:
            nearest = min(range(k), key=lambda ci: _euclidean(vec, centroids[ci], dims))
            clusters[nearest].append((fid, vec))

        # Update centroids
        new_centroids = []
        for ci in range(k):
            members = clusters.get(ci, [])
            if members:
                new_c = {d: statistics.mean(m[1].get(d, 0) for m in members) for d in dims}
                new_centroids.append(new_c)
            else:
                new_centroids.append(centroids[ci])
        centroids = new_centroids

    # Build result
    result_clusters = []
    for ci, members in clusters.items():
        result_clusters.append(FacultyCluster(
            cluster_id=ci,
            label=_cluster_label(centroids[ci]),
            faculty_ids=[fid for fid, _ in members],
            centroid={d: round(v, 2) for d, v in centroids[ci].items()},
        ))
    return result_clusters


# ── System health KPIs ────────────────────────────────────────────────────────

async def get_system_health(db: AsyncSession, university: str | None = None) -> SystemHealthKPI:
    """Compute system-wide health metrics for University/Admin dashboards."""
    fac_query = select(FacultyProfile)
    if university:
        fac_query = fac_query.where(FacultyProfile.university == university)
    fac_result = await db.execute(fac_query)
    faculties = fac_result.scalars().all()

    fb_count_result = await db.execute(select(func.count(SubmissionRecord.id)))
    total_fb = fb_count_result.scalar() or 0

    nlp_done_result = await db.execute(
        select(func.count(FeedbackRecord.id)).where(FeedbackRecord.nlp_processed == True)
    )
    nlp_total_result = await db.execute(select(func.count(FeedbackRecord.id)))
    nlp_done = nlp_done_result.scalar() or 0
    nlp_total = nlp_total_result.scalar() or 0

    composites = [f.composite_score for f in faculties if f.composite_score is not None]
    strong, developing, needs = _band_counts(faculties)
    total_f = len(faculties)

    def pct(count: int) -> float:
        return round(count / total_f * 100, 1) if total_f else 0.0

    return SystemHealthKPI(
        total_faculties=total_f,
        total_feedback_submissions=total_fb,
        avg_composite_score=round(_safe_mean(composites), 2) if composites else None,
        participation_rate=round(total_fb / max(total_f * 10, 1), 2),  # rough estimate
        faculties_with_reports=len([f for f in faculties if f.composite_score is not None]),
        faculties_flagged=sum(1 for f in faculties if f.has_anomaly_flag),
        nlp_processed_rate=round(nlp_done / max(nlp_total, 1), 3),
        strong_pct=pct(strong),
        developing_pct=pct(developing),
        needs_support_pct=pct(needs),
    )
