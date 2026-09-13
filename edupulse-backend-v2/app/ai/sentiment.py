"""
Lightweight NLP: Sentiment analysis using VADER + language-aware rules.
Handles English, Malayalam, and code-mixed text without model downloads.
"""
import logging
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# ── VADER sentiment (ships with vaderSentiment, no downloads) ─────────────────
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    _vader = SentimentIntensityAnalyzer()
    VADER_AVAILABLE = True
except ImportError:
    VADER_AVAILABLE = False
    _vader = None
    logger.warning("vaderSentiment not installed — using rule-based fallback")

# ── Malayalam positive/negative keywords (common in Kerala classroom comments) ─
_ML_POSITIVE = frozenset([
    "നല്ല", "മികച്ച", "excellent", "super", "best", "great", "wonderful",
    "helpful", "clear", "punctual", "fair", "engaging", "motivated",
    "inspiring", "thorough", "kind", "responsive", "patient",
])

_ML_NEGATIVE = frozenset([
    "മോശം", "ശരിയല്ല", "boring", "confusing", "unclear", "late", "unfair",
    "strict", "rude", "slow", "fast", "skip", "absent", "biased",
    "difficult", "poor", "bad", "worst", "horrible", "useless", "waste",
    "never", "never available", "ignored", "dismissed",
])

_NEGATION_WORDS = frozenset(["not", "never", "no", "neither", "nor", "don't", "doesn't",
                              "wasn't", "isn't", "aren't", "won't", "wouldn't", "couldn't",
                              "shouldn't", "hardly", "barely", "scarcely"])


@dataclass
class SentimentResult:
    score: float          # -1.0 (very negative) to +1.0 (very positive)
    label: str            # "positive" | "negative" | "neutral"
    confidence: float     # 0.0–1.0
    language: str         # "en" | "ml" | "mixed" | "unknown"


def detect_language(text: str) -> str:
    """Lightweight language detection without langdetect download."""
    # Malayalam Unicode range: 0D00–0D7F
    ml_chars = sum(1 for c in text if '\u0D00' <= c <= '\u0D7F')
    if ml_chars > 3:
        en_words = len(re.findall(r'[a-zA-Z]{3,}', text))
        return "mixed" if en_words > 2 else "ml"
    return "en"


def _rule_based_sentiment(text: str) -> float:
    """
    Simple bag-of-words sentiment with basic negation handling.
    Returns score in [-1.0, +1.0].
    """
    words = re.findall(r'\b\w+\b', text.lower())
    pos_count = neg_count = 0
    i = 0
    while i < len(words):
        word = words[i]
        # Check for negation in a 3-word window before current word
        negated = any(words[max(0, i-3):i].count(n) > 0 for n in _NEGATION_WORDS)

        if word in _ML_POSITIVE:
            if negated:
                neg_count += 1
            else:
                pos_count += 1
        elif word in _ML_NEGATIVE:
            if negated:
                pos_count += 0.5  # "not bad" → weakly positive
            else:
                neg_count += 1
        i += 1

    total = pos_count + neg_count
    if total == 0:
        return 0.0
    return (pos_count - neg_count) / total


def analyze_sentiment(text: str) -> SentimentResult:
    """
    Analyze sentiment of a feedback comment.
    Uses VADER for English, rule-based for Malayalam/mixed.
    """
    if not text or len(text.strip()) < 3:
        return SentimentResult(score=0.0, label="neutral", confidence=0.5, language="unknown")

    lang = detect_language(text)

    # Use VADER for English content
    if lang == "en" and VADER_AVAILABLE:
        scores = _vader.polarity_scores(text)
        compound = scores["compound"]   # -1.0 to +1.0
        confidence = max(scores["pos"], scores["neg"], scores["neu"])
    else:
        compound = _rule_based_sentiment(text)
        confidence = 0.6  # rule-based is less certain

    # Classify
    if compound >= 0.05:
        label = "positive"
    elif compound <= -0.05:
        label = "negative"
    else:
        label = "neutral"

    return SentimentResult(
        score=round(compound, 4),
        label=label,
        confidence=round(confidence, 4),
        language=lang,
    )
