"""
Lightweight topic extraction using TF-IDF + keyword clustering.
Identifies recurring themes in feedback comments without model downloads.
"""
import re
import logging
import math
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Sequence

logger = logging.getLogger(__name__)

# ── Pre-defined topic clusters ────────────────────────────────────────────────
# Each topic has seed keywords. A comment is tagged to a topic if enough
# keywords appear (weighted by TF-IDF-like importance).
TOPIC_SEEDS: dict[str, list[str]] = {
    "explanation_clarity": [
        "explain", "clear", "understand", "concept", "follow", "comprehend",
        "example", "illustration", "diagram", "step by step", "simple",
    ],
    "teaching_method": [
        "method", "approach", "style", "technique", "interactive", "demo",
        "slide", "blackboard", "video", "activity", "lecture", "practical",
    ],
    "syllabus_coverage": [
        "syllabus", "topic", "cover", "complete", "skip", "portion",
        "chapter", "module", "curriculum", "unit",
    ],
    "student_interaction": [
        "question", "doubt", "answer", "interact", "encourage", "participate",
        "discussion", "respond", "feedback", "listen",
    ],
    "punctuality_attendance": [
        "time", "late", "absent", "class", "period", "punctual", "cancel",
        "irregular", "schedule", "attend",
    ],
    "assessment_fairness": [
        "exam", "test", "mark", "grade", "fair", "bias", "internal",
        "assignment", "rubric", "correction", "transparent",
    ],
    "approachability": [
        "helpful", "kind", "rude", "friendly", "approachable", "patient",
        "available", "support", "doubt clearance", "office hours",
    ],
    "preparation_knowledge": [
        "prepare", "knowledge", "expert", "subject", "research", "update",
        "reference", "textbook", "authority", "mastery",
    ],
    "motivation_inspiration": [
        "inspire", "motivate", "interest", "passion", "enthusiasm", "engaging",
        "boring", "dull", "energy", "encourage",
    ],
}

# Stop words to exclude from topic detection
_STOP_WORDS = frozenset([
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "should",
    "could", "can", "may", "might", "shall", "must", "and", "or", "but",
    "for", "so", "yet", "both", "either", "neither", "in", "on", "at",
    "to", "of", "from", "with", "by", "about", "this", "that", "these",
    "those", "it", "its", "my", "your", "our", "their", "his", "her",
    "we", "they", "he", "she", "i", "me", "him", "us", "them",
    "very", "really", "quite", "also", "too", "more", "most", "much",
    "teacher", "professor", "faculty", "sir", "madam", "class", "course",
    "subject", "student",
])

MIN_TOPIC_SCORE = 0.15  # Minimum relevance to include a topic


@dataclass
class TopicResult:
    topics: list[str] = field(default_factory=list)        # Top topic labels
    topic_scores: dict[str, float] = field(default_factory=dict)  # topic → relevance [0,1]


def _tokenize(text: str) -> list[str]:
    tokens = re.findall(r'\b[a-zA-Z\u0D00-\u0D7F]{3,}\b', text.lower())
    return [t for t in tokens if t not in _STOP_WORDS]


def _phrase_score(tokens: list[str], seed_phrases: list[str]) -> float:
    """Score how well a token list matches a topic's seed phrases."""
    total_score = 0.0
    for phrase in seed_phrases:
        phrase_tokens = phrase.lower().split()
        # Single-word match
        if len(phrase_tokens) == 1:
            count = tokens.count(phrase_tokens[0])
            # Inverse document frequency approximation
            idf = math.log(10 / (1 + 0.5))  # rough constant
            total_score += count * idf
        else:
            # Multi-word: check if all tokens present and in proximity
            if all(pt in tokens for pt in phrase_tokens):
                total_score += 2.0  # phrase match gets double weight
    return total_score


def extract_topics(text: str, max_topics: int = 3) -> TopicResult:
    """
    Extract the top topics from a single feedback comment.
    Returns a TopicResult with ranked topic labels.
    """
    if not text or len(text.strip()) < 10:
        return TopicResult()

    tokens = _tokenize(text)
    if not tokens:
        return TopicResult()

    raw_scores: dict[str, float] = {}
    for topic, seeds in TOPIC_SEEDS.items():
        score = _phrase_score(tokens, seeds)
        if score > 0:
            raw_scores[topic] = score

    if not raw_scores:
        return TopicResult()

    # Normalize to [0, 1]
    max_score = max(raw_scores.values())
    normalized = {t: round(s / max_score, 3) for t, s in raw_scores.items()}

    # Filter by minimum threshold and rank
    qualified = {t: s for t, s in normalized.items() if s >= MIN_TOPIC_SCORE}
    ranked = sorted(qualified.items(), key=lambda x: x[1], reverse=True)

    return TopicResult(
        topics=[t for t, _ in ranked[:max_topics]],
        topic_scores=dict(ranked[:max_topics]),
    )


def extract_corpus_topics(comments: Sequence[str], max_topics: int = 5) -> list[str]:
    """
    Aggregate topic extraction across multiple comments.
    Returns the most common topics across the corpus.
    """
    topic_counts: Counter = Counter()
    for comment in comments:
        if comment:
            result = extract_topics(comment, max_topics=5)
            for topic in result.topics:
                topic_counts[topic] += 1

    return [topic for topic, _ in topic_counts.most_common(max_topics)]
