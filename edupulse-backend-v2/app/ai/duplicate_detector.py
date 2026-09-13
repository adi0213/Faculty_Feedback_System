"""
Semantic duplicate detection using TF-IDF cosine similarity.
Identifies near-identical comments that may indicate coordinated submissions.
"""
import logging
import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Sequence

logger = logging.getLogger(__name__)

SIMILARITY_THRESHOLD = 0.85  # Cosine similarity above which comments are considered duplicates
MIN_TOKENS = 5               # Don't bother checking very short comments


@dataclass
class DuplicateResult:
    is_duplicate: bool
    similar_to: str | None    # ID of the reference comment
    similarity_score: float


def _tokenize(text: str) -> list[str]:
    return re.findall(r'\b[a-zA-Z\u0D00-\u0D7F]{2,}\b', text.lower())


def _tfidf_vector(tokens: list[str], idf: dict[str, float]) -> dict[str, float]:
    """Build a TF-IDF vector for a token list given pre-computed IDF values."""
    tf = Counter(tokens)
    total = len(tokens)
    return {t: (count / total) * idf.get(t, 1.0) for t, count in tf.items()}


def _cosine_similarity(vec_a: dict[str, float], vec_b: dict[str, float]) -> float:
    """Compute cosine similarity between two sparse TF-IDF vectors."""
    keys = set(vec_a) | set(vec_b)
    dot = sum(vec_a.get(k, 0.0) * vec_b.get(k, 0.0) for k in keys)
    mag_a = math.sqrt(sum(v**2 for v in vec_a.values()))
    mag_b = math.sqrt(sum(v**2 for v in vec_b.values()))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def _compute_idf(corpus: list[list[str]]) -> dict[str, float]:
    """Compute IDF values for a corpus of tokenized documents."""
    n = len(corpus)
    df: Counter = Counter()
    for tokens in corpus:
        for t in set(tokens):
            df[t] += 1
    return {t: math.log(n / (1 + count)) + 1 for t, count in df.items()}


def detect_duplicates(
    new_comment: str,
    existing_comments: list[tuple[str, str]],  # list of (feedback_id, comment_text)
) -> DuplicateResult:
    """
    Check if new_comment is semantically similar to any existing comment.
    existing_comments: pre-loaded comments from the same faculty/term.
    """
    if not new_comment or len(new_comment.strip()) < 3:
        return DuplicateResult(is_duplicate=False, similar_to=None, similarity_score=0.0)

    new_tokens = _tokenize(new_comment)
    if len(new_tokens) < MIN_TOKENS:
        return DuplicateResult(is_duplicate=False, similar_to=None, similarity_score=0.0)

    valid_existing = [
        (fid, text) for fid, text in existing_comments
        if text and len(_tokenize(text)) >= MIN_TOKENS
    ]
    if not valid_existing:
        return DuplicateResult(is_duplicate=False, similar_to=None, similarity_score=0.0)

    # Build corpus for IDF computation
    all_token_lists = [new_tokens] + [_tokenize(text) for _, text in valid_existing]
    idf = _compute_idf(all_token_lists)

    new_vec = _tfidf_vector(new_tokens, idf)

    best_score = 0.0
    best_id = None
    for fid, text in valid_existing:
        existing_tokens = _tokenize(text)
        existing_vec = _tfidf_vector(existing_tokens, idf)
        sim = _cosine_similarity(new_vec, existing_vec)
        if sim > best_score:
            best_score = sim
            best_id = fid

    is_dup = best_score >= SIMILARITY_THRESHOLD

    return DuplicateResult(
        is_duplicate=is_dup,
        similar_to=best_id if is_dup else None,
        similarity_score=round(best_score, 4),
    )
