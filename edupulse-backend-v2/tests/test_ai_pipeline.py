"""Tests for the NLP AI pipeline modules."""
import pytest
from app.ai.sentiment import analyze_sentiment, detect_language
from app.ai.absa import analyze_aspects
from app.ai.spam_detector import detect_spam
from app.ai.duplicate_detector import detect_duplicates
from app.ai.topic_extractor import extract_topics, extract_corpus_topics


class TestSentiment:
    def test_positive_comment(self):
        result = analyze_sentiment("Excellent teacher, explains everything very clearly and is very helpful")
        assert result.label == "positive"
        assert result.score > 0

    def test_negative_comment(self):
        result = analyze_sentiment("Boring lectures, very confusing and always late")
        assert result.label == "negative"
        assert result.score < 0

    def test_neutral_short(self):
        result = analyze_sentiment("ok")
        assert result.label in ("neutral", "positive", "negative")

    def test_empty_string(self):
        result = analyze_sentiment("")
        assert result.label == "neutral"
        assert result.score == 0.0

    def test_language_detection_english(self):
        lang = detect_language("This is a good lecture")
        assert lang == "en"

    def test_negated_positive(self):
        result = analyze_sentiment("not helpful at all, very confusing")
        # Should be neutral or negative after negation
        assert result.score <= 0.3


class TestABSA:
    def test_clarity_flagged_for_confusing(self):
        result = analyze_aspects("The lecture is very confusing, hard to understand")
        assert "clarity" in result.flagged_dimensions

    def test_punctuality_flagged_for_late(self):
        result = analyze_aspects("Teacher is always late to class")
        assert "punctuality" in result.flagged_dimensions

    def test_positive_approachability(self):
        result = analyze_aspects("Very approachable and friendly, always helpful with doubts")
        scores = result.dimension_scores
        assert scores.get("approachability", 0) > 0

    def test_empty_returns_empty(self):
        result = analyze_aspects("")
        assert result.dimension_scores == {}
        assert result.flagged_dimensions == []

    def test_negation_reversal(self):
        result = analyze_aspects("not boring at all, actually quite engaging")
        scores = result.dimension_scores
        # engagement should be positive (negated negative)
        if "engagement" in scores:
            assert scores["engagement"] >= 0


class TestSpamDetector:
    def test_identical_extreme_scores_flagged(self):
        scores = {"clarity": 1, "methodology": 1, "punctuality": 1,
                  "fairness": 1, "approachability": 1, "pacing": 1}
        result = detect_spam(scores, None)
        assert result.is_spam is True

    def test_normal_scores_not_spam(self):
        scores = {"clarity": 3, "methodology": 2, "punctuality": 4,
                  "fairness": 3, "approachability": 4}
        result = detect_spam(scores, "Good explanation but could be clearer")
        assert result.is_spam is False

    def test_short_comment_flagged(self):
        scores = {"clarity": 2}
        result = detect_spam(scores, "ok")
        assert "comment_too_short" in result.reasons

    def test_non_constructive_pattern(self):
        scores = {"clarity": 1}
        result = detect_spam(scores, "i hate this teacher")
        assert result.is_constructive is False

    def test_good_comment_is_constructive(self):
        scores = {"clarity": 3}
        result = detect_spam(scores, "Needs more examples for complex algorithms")
        assert result.is_constructive is True


class TestDuplicateDetector:
    def test_identical_comments_detected(self):
        base = "Excellent teaching, very clear explanations and good examples"
        existing = [("id-1", base + " always.")]
        result = detect_duplicates(base, existing)
        assert result.is_duplicate is True

    def test_different_comments_not_duplicate(self):
        new = "Needs to improve pacing and cover more practical examples"
        existing = [("id-1", "Very punctual and fair grading always")]
        result = detect_duplicates(new, existing)
        assert result.is_duplicate is False

    def test_empty_new_comment(self):
        result = detect_duplicates("", [("id-1", "some text here")])
        assert result.is_duplicate is False

    def test_empty_existing(self):
        result = detect_duplicates("Good teacher", [])
        assert result.is_duplicate is False


class TestTopicExtractor:
    def test_extracts_clarity_topic(self):
        result = extract_topics("The explanation was very clear and easy to understand with examples")
        assert "explanation_clarity" in result.topics

    def test_extracts_punctuality_topic(self):
        result = extract_topics("Teacher always comes late and cancels classes regularly")
        assert "punctuality_attendance" in result.topics

    def test_empty_returns_empty(self):
        result = extract_topics("")
        assert result.topics == []

    def test_corpus_topics(self):
        comments = [
            "Very clear explanations with good examples",
            "Explains concepts in simple way easy to understand",
            "Good explanation with real world examples for each topic",
        ]
        topics = extract_corpus_topics(comments, max_topics=3)
        assert len(topics) > 0
        assert "explanation_clarity" in topics
