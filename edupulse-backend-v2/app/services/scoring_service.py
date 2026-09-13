"""
Statistical Scoring Engine — the core of the evaluation system.

Implements, in order:
1. Winsorizing (capping extreme values at 5th/95th percentile)
2. Cohort z-score normalization (vs. peers in same dept/term)
3. Empirical Bayes shrinkage (for small response counts)
4. Temporal cluster anomaly detection
5. Composite score calculation (α-weighted objective + sentiment)
6. Band classification (strong / developing / needs_support)
7. Confidence interval estimation

All governance parameters (α, k, winsor percentiles) come from Settings,
so they can be adjusted by the oversight committee without code changes.
"""
import json
import logging
import math
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Sequence

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.faculty import FacultyProfile
from app.models.feedback import FeedbackRecord

logger = logging.getLogger(__name__)
settings = get_settings()

SCORE_DIMENSIONS = [
    "clarity", "methodology", "punctuality", "fairness",
    "approachability", "pacing", "engagement", "practical",
    "assessment", "overall",
]

# Map 1-4 Likert scale → 1-5 for display
def likert_to_five(v: float) -> float:
    return round(1.0 + (v - 1.0) * (4.0 / 3.0), 3)


@dataclass
class ScoringResult:
    faculty_profile_id: str
    term: str
    response_count: int

    # Raw mean per dimension (1-4 scale)
    raw_means: dict[str, float] = field(default_factory=dict)

    # Winsorized means
    winsorized_means: dict[str, float] = field(default_factory=dict)

    # Cohort z-scores
    z_scores: dict[str, float] = field(default_factory=dict)

    # Empirical Bayes shrunk means (the primary display value)
    shrunk_means: dict[str, float] = field(default_factory=dict)

    # Sentiment aggregate
    mean_sentiment: float | None = None

    # Composite score (α·objective + (1-α)·sentiment), mapped to 1-5
    composite_score: float | None = None

    # Classification
    score_band: str = "needs_support"  # strong | developing | needs_support

    # Confidence
    confidence_label: str = "low"     # high | medium | low
    std_error: float | None = None

    # Anomaly
    has_temporal_anomaly: bool = False
    anomaly_details: str | None = None

    # For display: per-dimension 1-5 scale
    display_scores: dict[str, float] = field(default_factory=dict)


# ── 1. Winsorizing ─────────────────────────────────────────────────────────────
def winsorize(values: list[float], low_pct: int = 5, high_pct: int = 95) -> list[float]:
    """
    Cap extreme values at the specified percentiles.
    Returns a new list with extremes replaced by the percentile cap.
    """
    if len(values) < 4:
        return values  # Not enough data to winsorize meaningfully
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    low_idx = max(0, int(n * low_pct / 100) - 1)
    high_idx = min(n - 1, int(n * high_pct / 100))
    low_cap = sorted_vals[low_idx]
    high_cap = sorted_vals[high_idx]
    return [max(low_cap, min(high_cap, v)) for v in values]


def _safe_mean(values: list[float]) -> float | None:
    if not values:
        return None
    return statistics.mean(values)


# ── 2. Cohort z-score normalization ───────────────────────────────────────────
def compute_z_score(faculty_mean: float, cohort_mean: float, cohort_std: float) -> float:
    """
    Normalized position vs cohort. Zero means at the cohort average.
    Returns 0 if cohort_std is too small (avoids division by near-zero).
    """
    if cohort_std < 0.01:
        return 0.0
    return round((faculty_mean - cohort_mean) / cohort_std, 4)


# ── 3. Empirical Bayes shrinkage ───────────────────────────────────────────────
def empirical_bayes_shrink(
    faculty_mean: float,
    cohort_mean: float,
    n: int,
    k: int = 8,
) -> float:
    """
    Shrunk_Score = (n / (n + k)) * Faculty_Mean + (k / (n + k)) * Cohort_Mean
    k is the governance-set prior sample size (default 8).
    When n is large, the result approaches Faculty_Mean.
    When n is small, it shrinks toward the cohort mean.
    """
    weight = n / (n + k)
    return round(weight * faculty_mean + (1 - weight) * cohort_mean, 4)


# ── 4. Temporal anomaly detection ─────────────────────────────────────────────
def detect_temporal_anomaly(
    timestamps: list[datetime],
    total_count: int,
    window_hours: int = 24,
    threshold: float = 0.5,
) -> tuple[bool, str | None]:
    """
    Flag if more than `threshold` fraction of responses arrive within
    a `window_hours` window (possible coordinated attack or grade-retaliation burst).
    """
    if total_count < 5 or not timestamps:
        return False, None

    for i, ts in enumerate(timestamps):
        window_end = ts + timedelta(hours=window_hours)
        in_window = sum(1 for t in timestamps if ts <= t <= window_end)
        if in_window / total_count >= threshold:
            return True, (
                f"{in_window} of {total_count} responses arrived within "
                f"{window_hours}h starting {ts.strftime('%Y-%m-%d %H:%M')} UTC"
            )
    return False, None


# ── 5. Confidence estimation ───────────────────────────────────────────────────
def estimate_confidence(n: int, std_dev: float | None) -> tuple[str, float | None]:
    """
    Returns (label, standard_error).
    high: n ≥ 20 and low variance
    medium: n ≥ 10
    low: n < 10
    """
    if n < 5:
        return "low", None
    se = (std_dev / math.sqrt(n)) if std_dev and std_dev > 0 else None
    if n >= 20 and (se is None or se < 0.3):
        return "high", se
    if n >= 10:
        return "medium", se
    return "low", se


# ── 6. Band classification ─────────────────────────────────────────────────────
def classify_band(composite: float, cohort_mean: float, cohort_std: float) -> str:
    """
    Assign band using control chart limits:
    strong:        composite > cohort_mean + 0.5 * cohort_std  (or > 4.0)
    needs_support: composite < cohort_mean - 0.5 * cohort_std  (or < 2.5)
    developing:    everything else
    """
    upper = cohort_mean + 0.5 * max(cohort_std, 0.3)
    lower = cohort_mean - 0.5 * max(cohort_std, 0.3)
    if composite >= upper or composite >= 4.0:
        return "strong"
    if composite <= lower or composite <= 2.5:
        return "needs_support"
    return "developing"


# ── Main scoring function ──────────────────────────────────────────────────────
async def compute_faculty_scores(
    db: AsyncSession,
    faculty_profile_id: str,
    term: str,
) -> ScoringResult | None:
    """
    Run the full scoring pipeline for one faculty/term combination.
    Returns None if k-anonymity threshold not yet met.
    """
    # ── Load all valid feedback ───────────────────────────────────────────────
    fb_result = await db.execute(
        select(FeedbackRecord).where(
            FeedbackRecord.faculty_profile_id == faculty_profile_id,
            FeedbackRecord.term == term,
            FeedbackRecord.is_spam == False,
        )
    )
    records: list[FeedbackRecord] = fb_result.scalars().all()
    n = len(records)

    if n < settings.k_anonymity_threshold:
        logger.info("Scoring skipped: k-anonymity not met (%d/%d)", n, settings.k_anonymity_threshold)
        return None

    # ── Parse scores ──────────────────────────────────────────────────────────
    dim_values: dict[str, list[float]] = {d: [] for d in SCORE_DIMENSIONS}
    sentiment_values: list[float] = []
    timestamps: list[datetime] = []

    for rec in records:
        try:
            scores: dict = json.loads(rec.scores_json)
        except (json.JSONDecodeError, TypeError):
            continue
        for dim in SCORE_DIMENSIONS:
            if dim in scores:
                dim_values[dim].append(float(scores[dim]))
        if rec.sentiment_score is not None:
            sentiment_values.append(float(rec.sentiment_score))
        if rec.submitted_at:
            timestamps.append(rec.submitted_at)

    # ── Step 1: Raw means ─────────────────────────────────────────────────────
    raw_means: dict[str, float] = {}
    for dim, vals in dim_values.items():
        m = _safe_mean(vals)
        if m is not None:
            raw_means[dim] = round(m, 4)

    if not raw_means:
        return None

    # ── Step 2: Winsorizing ───────────────────────────────────────────────────
    winsorized_means: dict[str, float] = {}
    for dim, vals in dim_values.items():
        if vals:
            w = winsorize(vals, settings.scoring_winsor_low, settings.scoring_winsor_high)
            m = _safe_mean(w)
            if m is not None:
                winsorized_means[dim] = round(m, 4)

    # ── Step 3: Load cohort data for normalization ────────────────────────────
    fac_result = await db.execute(
        select(FacultyProfile).where(FacultyProfile.id == faculty_profile_id)
    )
    faculty = fac_result.scalar_one_or_none()
    if not faculty:
        return None

    # Get all faculties in same dept/term for cohort
    cohort_result = await db.execute(
        select(FacultyProfile).where(
            FacultyProfile.dept == faculty.dept,
            FacultyProfile.college == faculty.college,
        )
    )
    cohort_faculties = cohort_result.scalars().all()

    # Collect cohort composite scores
    cohort_composites: list[float] = []
    for cf in cohort_faculties:
        if cf.composite_score is not None and cf.id != faculty_profile_id:
            cohort_composites.append(cf.composite_score)

    cohort_mean = statistics.mean(cohort_composites) if cohort_composites else 3.0
    cohort_std = statistics.stdev(cohort_composites) if len(cohort_composites) > 1 else 0.5

    # ── Step 4: Z-scores ──────────────────────────────────────────────────────
    z_scores: dict[str, float] = {}
    for dim, val in winsorized_means.items():
        z_scores[dim] = compute_z_score(val, cohort_mean, cohort_std)

    # ── Step 5: Empirical Bayes shrinkage ─────────────────────────────────────
    shrunk_means: dict[str, float] = {}
    for dim, val in winsorized_means.items():
        shrunk_means[dim] = empirical_bayes_shrink(
            val, cohort_mean, n, settings.scoring_bayes_k
        )

    # ── Step 6: Objective composite (mean of shrunk dimension scores) ─────────
    objective_raw = statistics.mean(shrunk_means.values()) if shrunk_means else cohort_mean
    # Map from 1-4 scale to 1-5 for display
    objective_5 = likert_to_five(objective_raw)

    # ── Step 7: Sentiment composite ───────────────────────────────────────────
    if sentiment_values:
        # Sentiment is -1 to +1, map to 1-5: score_5 = 3 + sentiment * 2
        mean_sentiment = statistics.mean(sentiment_values)
        sentiment_5 = round(3.0 + mean_sentiment * 2.0, 4)
        sentiment_5 = max(1.0, min(5.0, sentiment_5))
    else:
        mean_sentiment = None
        sentiment_5 = objective_5  # Fallback: use objective when no comments

    # ── Step 8: Composite score ───────────────────────────────────────────────
    alpha = settings.scoring_alpha
    composite = round(alpha * objective_5 + (1 - alpha) * sentiment_5, 4)
    composite = max(1.0, min(5.0, composite))

    # ── Step 9: Temporal anomaly detection ───────────────────────────────────
    has_anomaly, anomaly_details = detect_temporal_anomaly(
        timestamps, n,
        settings.temporal_cluster_window_hours,
        settings.temporal_cluster_threshold,
    )

    # ── Step 10: Band and confidence ─────────────────────────────────────────
    band = classify_band(composite, cohort_mean, cohort_std)
    all_vals = [v for vals in dim_values.values() for v in vals]
    try:
        std_dev = statistics.stdev(all_vals) if len(all_vals) > 1 else None
    except statistics.StatisticsError:
        std_dev = None
    confidence_label, std_error = estimate_confidence(n, std_dev)

    # ── Display scores (1-5 scale) ────────────────────────────────────────────
    display_scores = {dim: likert_to_five(v) for dim, v in shrunk_means.items()}

    return ScoringResult(
        faculty_profile_id=faculty_profile_id,
        term=term,
        response_count=n,
        raw_means=raw_means,
        winsorized_means=winsorized_means,
        z_scores=z_scores,
        shrunk_means=shrunk_means,
        mean_sentiment=mean_sentiment,
        composite_score=composite,
        score_band=band,
        confidence_label=confidence_label,
        std_error=std_error,
        has_temporal_anomaly=has_anomaly,
        anomaly_details=anomaly_details,
        display_scores=display_scores,
    )


async def update_faculty_profile_scores(
    db: AsyncSession,
    faculty_profile_id: str,
    term: str,
) -> ScoringResult | None:
    """
    Run scoring and persist results back to the FacultyProfile.
    Called after each batch of NLP processing is complete.
    """
    result = await compute_faculty_scores(db, faculty_profile_id, term)
    if result is None:
        return None

    fac_result = await db.execute(
        select(FacultyProfile).where(FacultyProfile.id == faculty_profile_id)
    )
    faculty = fac_result.scalar_one_or_none()
    if not faculty:
        return None

    faculty.dimension_scores_json = json.dumps(result.display_scores)
    faculty.composite_score = result.composite_score
    faculty.score_band = result.score_band
    faculty.has_anomaly_flag = result.has_temporal_anomaly
    faculty.anomaly_details_json = (
        json.dumps({"details": result.anomaly_details}) if result.anomaly_details else None
    )
    faculty.response_count = result.response_count

    # Update trend
    try:
        trend = json.loads(faculty.score_trend_json) if faculty.score_trend_json else []
    except (json.JSONDecodeError, TypeError):
        trend = []

    # Replace or append current term
    trend = [t for t in trend if t.get("term") != term]
    trend.append({
        "term": term,
        "composite_score": result.composite_score,
        "response_count": result.response_count,
        "score_band": result.score_band,
    })
    faculty.score_trend_json = json.dumps(sorted(trend, key=lambda x: x["term"]))

    db.add(faculty)
    logger.info(
        "Faculty %s scores updated: composite=%.2f band=%s n=%d",
        faculty_profile_id, result.composite_score, result.score_band, result.response_count,
    )
    return result
