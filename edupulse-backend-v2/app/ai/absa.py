"""
Aspect-Based Sentiment Analysis (ABSA) — lightweight, rule-based.
Maps comment text to specific teaching dimensions with polarity scores.
No model downloads required.
"""
import re
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# ── Dimension keyword lexicon ─────────────────────────────────────────────────
# Each dimension has positive and negative trigger words/phrases.
DIMENSION_LEXICON: dict[str, dict[str, list[str]]] = {
    "clarity": {
        "positive": [
            "clear", "clear explanation", "explains well", "easy to understand",
            "crystal clear", "well explained", "good examples", "vivid",
            "simplified", "understandable", "comprehensible", "logical",
        ],
        "negative": [
            "confusing", "unclear", "hard to follow", "difficult to understand",
            "too technical", "jargon", "messy", "disorganized", "jumbled",
            "no examples", "fast", "too fast", "slow", "too slow",
        ],
    },
    "methodology": {
        "positive": [
            "interactive", "engaging", "innovative", "creative", "hands-on",
            "visual", "multimedia", "demonstration", "case study", "practical",
            "real world", "project", "activity", "collaborative",
        ],
        "negative": [
            "boring", "monotonous", "reads slides", "dictates", "no interaction",
            "lecture only", "chalk and talk", "outdated", "repetitive",
            "no demo", "theoretical only", "rote",
        ],
    },
    "punctuality": {
        "positive": [
            "on time", "punctual", "starts on time", "ends on time",
            "regular", "consistent", "full hours", "complete syllabus",
        ],
        "negative": [
            "late", "delay", "absent", "cancelled", "never comes",
            "irregular", "skips class", "ends early", "incomplete",
            "misses", "bunks",
        ],
    },
    "fairness": {
        "positive": [
            "fair", "transparent", "unbiased", "consistent grading",
            "clear rubric", "feedback on marks", "rechecking", "impartial",
        ],
        "negative": [
            "unfair", "biased", "partial", "favoritism", "inconsistent",
            "no feedback", "arbitrary", "out of syllabus", "no criteria",
            "subjective", "discrimination",
        ],
    },
    "approachability": {
        "positive": [
            "approachable", "friendly", "helpful", "available", "supportive",
            "kind", "patient", "responsive", "open door", "encourages questions",
        ],
        "negative": [
            "unapproachable", "rude", "harsh", "dismissive", "unavailable",
            "ignores", "mocks", "discourages", "never available", "intimidating",
            "scary", "angry", "shouts",
        ],
    },
    "pacing": {
        "positive": [
            "good pace", "well planned", "adequate coverage", "on schedule",
            "proper timing", "systematic", "balanced",
        ],
        "negative": [
            "rush", "rushed", "too fast", "racing", "incomplete syllabus",
            "topics skipped", "too slow", "behind schedule", "marathon",
            "last minute", "cramming at end",
        ],
    },
    "engagement": {
        "positive": [
            "participative", "interactive", "encourages", "motivates",
            "energetic", "enthusiastic", "inspiring", "student involvement",
        ],
        "negative": [
            "boring", "dull", "no participation", "one-sided", "not engaging",
            "low energy", "distracted", "uninterested",
        ],
    },
}

NEGATION_WINDOW = 3  # look back this many tokens for negation
_NEGATION_TOKENS = frozenset(["not", "never", "no", "neither", "nor", "don't",
                               "doesn't", "wasn't", "isn't", "aren't", "won't",
                               "wouldn't", "couldn't", "shouldn't"])


@dataclass
class ABSAResult:
    """Aspect-based sentiment result for a comment."""
    dimension_scores: dict[str, float] = field(default_factory=dict)  # dim → [-1, +1]
    flagged_dimensions: list[str] = field(default_factory=list)       # dims with negative signal
    mentioned_dimensions: list[str] = field(default_factory=list)     # any mention


def _tokenize(text: str) -> list[str]:
    return re.findall(r'\b\w+\b', text.lower())


def _phrase_matches(tokens: list[str], phrases: list[str]) -> list[tuple[int, str]]:
    """Find all phrase matches and return (token_index, phrase) tuples."""
    matches = []
    for phrase in phrases:
        phrase_tokens = phrase.lower().split()
        n = len(phrase_tokens)
        for i in range(len(tokens) - n + 1):
            if tokens[i:i+n] == phrase_tokens:
                matches.append((i, phrase))
    return matches


def analyze_aspects(text: str) -> ABSAResult:
    """
    Run ABSA on a comment text. Returns per-dimension sentiment scores
    and lists of flagged / mentioned dimensions.
    """
    if not text or len(text.strip()) < 3:
        return ABSAResult()

    tokens = _tokenize(text)
    dim_signals: dict[str, list[float]] = {d: [] for d in DIMENSION_LEXICON}

    for dim, lexicon in DIMENSION_LEXICON.items():
        for polarity, phrases in [("positive", lexicon["positive"]),
                                  ("negative", lexicon["negative"])]:
            score = 1.0 if polarity == "positive" else -1.0
            for match_idx, phrase in _phrase_matches(tokens, phrases):
                # Check for negation in window before match
                window_start = max(0, match_idx - NEGATION_WINDOW)
                window = tokens[window_start:match_idx]
                negated = any(t in _NEGATION_TOKENS for t in window)
                effective_score = -score if negated else score
                dim_signals[dim].append(effective_score)

    # Aggregate per dimension
    result = ABSAResult()
    for dim, signals in dim_signals.items():
        if signals:
            avg = sum(signals) / len(signals)
            result.dimension_scores[dim] = round(avg, 3)
            result.mentioned_dimensions.append(dim)
            if avg < -0.1:
                result.flagged_dimensions.append(dim)

    return result
