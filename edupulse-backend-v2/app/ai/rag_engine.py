"""
Lightweight RAG engine using TF-IDF cosine similarity.
Retrieves the most relevant courses from the catalog for a given query context.
Falls back gracefully when pgvector is unavailable.
"""
import json
import logging
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.course_catalog import CourseCatalogEntry, CourseEmbedding

logger = logging.getLogger(__name__)

CATALOG_PATH = Path(__file__).parent.parent.parent / "data" / "course_catalog.json"

_STOP_WORDS = frozenset([
    "the", "a", "an", "is", "are", "was", "were", "and", "or", "but",
    "for", "in", "on", "at", "to", "of", "with", "by", "this", "that",
    "it", "be", "do", "have", "will", "would", "can", "could", "should",
    "may", "might", "from", "as", "if", "which", "when", "where", "how",
    "who", "what", "than", "more", "most", "also", "not", "no",
])


@dataclass
class RetrievedCourse:
    course_id: str
    title: str
    provider: str
    institution: str | None
    url: str | None
    duration_label: str | None
    primary_dimension: str | None
    description: str
    learning_outcomes: list[str]
    similarity_score: float


def _tokenize(text: str) -> list[str]:
    tokens = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    return [t for t in tokens if t not in _STOP_WORDS]


def _build_idf(corpus: list[list[str]]) -> dict[str, float]:
    n = len(corpus)
    df: Counter = Counter()
    for doc in corpus:
        for t in set(doc):
            df[t] += 1
    return {t: math.log(n / (1 + count)) + 1.0 for t, count in df.items()}


def _tfidf_vec(tokens: list[str], idf: dict[str, float]) -> dict[str, float]:
    tf = Counter(tokens)
    total = max(len(tokens), 1)
    return {t: (count / total) * idf.get(t, 1.0) for t, count in tf.items()}


def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
    keys = set(a) & set(b)
    dot = sum(a[k] * b[k] for k in keys)
    mag_a = math.sqrt(sum(v ** 2 for v in a.values()))
    mag_b = math.sqrt(sum(v ** 2 for v in b.values()))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return round(dot / (mag_a * mag_b), 4)


class TFIDFRagEngine:
    """
    In-memory TF-IDF RAG engine built from the course catalog.
    Re-initialized at startup and when catalog is updated.
    """

    def __init__(self):
        self._courses: list[dict] = []
        self._tokens: list[list[str]] = []
        self._idf: dict[str, float] = {}
        self._loaded = False

    def load_from_json(self, path: Path = CATALOG_PATH) -> None:
        """Load catalog from JSON file (used in development without DB)."""
        with open(path, encoding="utf-8") as f:
            self._courses = json.load(f)
        self._build_index()
        logger.info("RAG engine loaded %d courses from JSON", len(self._courses))

    def load_from_records(self, records: list[CourseCatalogEntry]) -> None:
        """Load catalog from SQLAlchemy ORM records."""
        self._courses = []
        for r in records:
            outcomes = []
            try:
                outcomes = json.loads(r.learning_outcomes_json) if r.learning_outcomes_json else []
            except (json.JSONDecodeError, TypeError):
                pass
            self._courses.append({
                "id": r.id,
                "title": r.title,
                "provider": r.provider,
                "institution": r.institution,
                "url": r.url,
                "duration_label": r.duration_label,
                "primary_dimension": r.primary_dimension,
                "description": r.description,
                "learning_outcomes": outcomes,
            })
        self._build_index()
        logger.info("RAG engine loaded %d courses from DB", len(self._courses))

    def _build_index(self) -> None:
        """Build TF-IDF index from loaded courses."""
        self._tokens = []
        for course in self._courses:
            text = " ".join([
                course.get("title", ""),
                course.get("description", ""),
                course.get("primary_dimension", ""),
                " ".join(course.get("secondary_dimensions", [])),
                " ".join(course.get("learning_outcomes", [])),
            ])
            self._tokens.append(_tokenize(text))
        self._idf = _build_idf(self._tokens)
        self._loaded = True

    def retrieve(
        self,
        query: str,
        target_dimensions: list[str] | None = None,
        top_k: int = 6,
        min_similarity: float = 0.05,
    ) -> list[RetrievedCourse]:
        """
        Retrieve the top-k most relevant courses for a query string.
        Optionally boosts courses targeting specific dimensions.
        """
        if not self._loaded:
            self.load_from_json()

        query_tokens = _tokenize(query)
        if not query_tokens:
            return []

        query_vec = _tfidf_vec(query_tokens, self._idf)

        scored: list[tuple[float, int]] = []
        for idx, course_tokens in enumerate(self._tokens):
            doc_vec = _tfidf_vec(course_tokens, self._idf)
            sim = _cosine(query_vec, doc_vec)

            # Boost if course targets a requested dimension
            if target_dimensions:
                primary = self._courses[idx].get("primary_dimension", "")
                secondary = self._courses[idx].get("secondary_dimensions", [])
                if primary in target_dimensions or any(d in target_dimensions for d in secondary):
                    sim = min(1.0, sim + 0.15)

            if sim >= min_similarity:
                scored.append((sim, idx))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = []
        for sim, idx in scored[:top_k]:
            c = self._courses[idx]
            results.append(RetrievedCourse(
                course_id=c.get("id", f"catalog_{idx}"),
                title=c["title"],
                provider=c["provider"],
                institution=c.get("institution"),
                url=c.get("url"),
                duration_label=c.get("duration_label"),
                primary_dimension=c.get("primary_dimension"),
                description=c["description"],
                learning_outcomes=c.get("learning_outcomes", []),
                similarity_score=sim,
            ))
        return results


# Module-level singleton
_rag_engine: TFIDFRagEngine | None = None


def get_rag_engine() -> TFIDFRagEngine:
    global _rag_engine
    if _rag_engine is None:
        _rag_engine = TFIDFRagEngine()
        _rag_engine.load_from_json()
    return _rag_engine
