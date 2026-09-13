"""Tests for the statistical scoring engine."""
import pytest
import math
from app.services.scoring_service import (
    winsorize,
    compute_z_score,
    empirical_bayes_shrink,
    detect_temporal_anomaly,
    classify_band,
    estimate_confidence,
    likert_to_five,
)
from datetime import datetime, timezone, timedelta


class TestWinsorize:
    def test_caps_extreme_values(self):
        vals = [1, 1, 3, 3, 3, 3, 4, 4, 4, 10]
        result = winsorize(vals, low_pct=10, high_pct=80)
        assert max(result) < 10  # extreme capped

    def test_no_change_for_normal_distribution(self):
        vals = [2, 3, 3, 3, 3, 3, 4]
        result = winsorize(vals)
        assert result == vals

    def test_too_few_values_unchanged(self):
        vals = [1, 4]
        assert winsorize(vals) == vals

    def test_symmetric_capping(self):
        vals = [1, 2, 3, 3, 3, 4, 100]
        result = winsorize(vals, low_pct=10, high_pct=80)
        assert all(v <= 4 for v in result)  # No value beyond original range distribution


class TestEmpiricalBayes:
    def test_shrinks_toward_cohort_for_small_n(self):
        faculty_mean = 4.5
        cohort_mean = 3.0
        shrunk = empirical_bayes_shrink(faculty_mean, cohort_mean, n=3, k=8)
        assert shrunk < faculty_mean
        assert shrunk > cohort_mean

    def test_approaches_faculty_mean_for_large_n(self):
        faculty_mean = 4.5
        cohort_mean = 3.0
        shrunk = empirical_bayes_shrink(faculty_mean, cohort_mean, n=1000, k=8)
        assert abs(shrunk - faculty_mean) < 0.1

    def test_equals_cohort_at_n_zero(self):
        shrunk = empirical_bayes_shrink(4.0, 3.0, n=0, k=8)
        assert shrunk == 3.0

    def test_formula_correctness(self):
        """Verify Shrunk = (n/(n+k)) * fac + (k/(n+k)) * cohort"""
        n, k = 8, 8
        fac, cohort = 4.0, 3.0
        expected = (n / (n + k)) * fac + (k / (n + k)) * cohort
        result = empirical_bayes_shrink(fac, cohort, n, k)
        assert abs(result - expected) < 0.001


class TestZScore:
    def test_above_average_positive(self):
        z = compute_z_score(4.0, 3.0, 0.5)
        assert z > 0

    def test_at_average_zero(self):
        z = compute_z_score(3.0, 3.0, 0.5)
        assert z == 0.0

    def test_near_zero_std_returns_zero(self):
        z = compute_z_score(4.0, 3.0, 0.001)
        assert z == 0.0


class TestBandClassification:
    def test_strong_band(self):
        assert classify_band(4.5, 3.5, 0.5) == "strong"

    def test_needs_support_band(self):
        assert classify_band(2.0, 3.5, 0.5) == "needs_support"

    def test_developing_band(self):
        assert classify_band(3.5, 3.5, 0.5) == "developing"

    def test_high_score_always_strong(self):
        assert classify_band(4.1, 2.0, 0.1) == "strong"

    def test_low_score_always_needs_support(self):
        assert classify_band(2.4, 4.0, 0.1) == "needs_support"


class TestTemporalAnomaly:
    def test_detects_burst(self):
        now = datetime.now(timezone.utc)
        # 8 responses within 2 hours, total 10
        timestamps = [now - timedelta(hours=1)] * 8 + [now - timedelta(days=10)] * 2
        has_anomaly, details = detect_temporal_anomaly(timestamps, total_count=10)
        assert has_anomaly is True
        assert details is not None

    def test_no_anomaly_spread_out(self):
        now = datetime.now(timezone.utc)
        timestamps = [now - timedelta(days=i * 3) for i in range(10)]
        has_anomaly, _ = detect_temporal_anomaly(timestamps, total_count=10)
        assert has_anomaly is False

    def test_small_count_not_flagged(self):
        now = datetime.now(timezone.utc)
        timestamps = [now] * 3
        has_anomaly, _ = detect_temporal_anomaly(timestamps, total_count=3)
        assert has_anomaly is False


class TestLikertConversion:
    def test_one_maps_to_one(self):
        assert likert_to_five(1.0) == 1.0

    def test_four_maps_to_five(self):
        assert likert_to_five(4.0) == 5.0

    def test_two_point_five_maps_to_three(self):
        assert abs(likert_to_five(2.5) - 3.0) < 0.01


class TestConfidence:
    def test_high_n_high_confidence(self):
        label, se = estimate_confidence(n=25, std_dev=0.4)
        assert label == "high"
        assert se is not None

    def test_low_n_low_confidence(self):
        label, _ = estimate_confidence(n=3, std_dev=0.5)
        assert label == "low"

    def test_medium_n_medium_confidence(self):
        label, _ = estimate_confidence(n=12, std_dev=0.8)
        assert label == "medium"
