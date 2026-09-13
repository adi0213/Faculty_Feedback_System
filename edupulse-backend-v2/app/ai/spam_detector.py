"""
Spam and low-quality feedback detection.
Uses statistical signals and heuristic rules — no ML model required.
"""
import re
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# ── Configuration thresholds ──────────────────────────────────────────────────
MIN_COMMENT_TOKENS = 3        # Spam if comment has fewer meaningful tokens
MAX_REPEAT_CHAR_RUN = 4       # "gooood" → spam
GIBBERISH_RATIO_THRESHOLD = 0.6  # Fraction of tokens that are nonsense
PROFANITY_BLOCK = frozenset([
    # Generic placeholder — in production, load from a curated moderation list
    "idiot", "stupid", "moron", "hate", "kill", "useless",
    "terrible", "worst ever", "dumb",
])
ALL_EXTREME_RATIO = 0.8       # Spam if >80% of scores are the same extreme value
EXTREME_VALUES = frozenset([1, 4])

# Non-constructive patterns (personal attack vs critique of teaching)
NON_CONSTRUCTIVE_PATTERNS = [
    r'\b(i hate|i dislike|stupid|idiot|bad person|disgusting|ugly)\b',
    r'\b(kill|die|fail)\b',
    r'^[a-zA-Z]{1,3}$',           # Single-word nonsense
    r'^[\W_]+$',                  # Only punctuation/symbols
    r'(.)\1{4,}',                 # Repeated characters: "aaaaaaa"
]


@dataclass
class SpamResult:
    is_spam: bool
    is_constructive: bool
    reasons: list[str]
    confidence: float             # 0.0–1.0


def detect_spam(
    scores: dict[str, int],
    comment: str | None,
) -> SpamResult:
    """
    Multi-signal spam/quality detector.
    Returns SpamResult with classification and reasons.
    """
    reasons: list[str] = []
    spam_signals = 0
    total_signals = 0

    # ── Signal 1: All extreme scores ─────────────────────────────────────────
    total_signals += 1
    if scores:
        values = list(scores.values())
        extreme_count = sum(1 for v in values if v in EXTREME_VALUES)
        if extreme_count / len(values) >= ALL_EXTREME_RATIO:
            # Check if all same value (more suspicious)
            if len(set(values)) == 1:
                spam_signals += 1
                reasons.append("all_scores_identical_extreme")

    # ── Signal 2: Comment quality ─────────────────────────────────────────────
    if comment:
        tokens = re.findall(r'\b[a-zA-Z\u0D00-\u0D7F]{2,}\b', comment.lower())
        total_signals += 1

        # Too short
        if len(tokens) < MIN_COMMENT_TOKENS:
            spam_signals += 0.5
            reasons.append("comment_too_short")

        # Repeated character runs
        if re.search(r'(.)\1{%d,}' % MAX_REPEAT_CHAR_RUN, comment):
            spam_signals += 0.5
            reasons.append("repeated_characters")

        # Non-constructive / personal attack patterns
        is_constructive = True
        for pattern in NON_CONSTRUCTIVE_PATTERNS:
            if re.search(pattern, comment, re.IGNORECASE):
                is_constructive = False
                reasons.append(f"non_constructive_pattern")
                spam_signals += 0.3
                break

        # Profanity check
        comment_words = set(comment.lower().split())
        if comment_words & PROFANITY_BLOCK:
            is_constructive = False
            spam_signals += 0.5
            reasons.append("profanity_detected")
    else:
        is_constructive = True  # No comment — can't judge constructiveness

    # ── Calculate overall ─────────────────────────────────────────────────────
    confidence = min(spam_signals / max(total_signals, 1), 1.0)
    is_spam = confidence >= 0.6

    return SpamResult(
        is_spam=is_spam,
        is_constructive=is_constructive,
        reasons=reasons,
        confidence=round(confidence, 3),
    )
