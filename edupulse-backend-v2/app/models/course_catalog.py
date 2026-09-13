"""
Course catalog and vector embedding models for RAG.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Index,
    Integer, String, Text,
)
from sqlalchemy.orm import relationship

from app.db.session import Base

try:
    from pgvector.sqlalchemy import Vector
    PGVECTOR_AVAILABLE = True
except ImportError:
    PGVECTOR_AVAILABLE = False
    Vector = None  # type: ignore


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class CourseCatalogEntry(Base):
    """
    Curated database of verified faculty development courses from
    NPTEL, SWAYAM, AICTE, UGC, IIT, and other recognized institutions.
    """
    __tablename__ = "course_catalog"
    __table_args__ = (
        Index("ix_course_catalog_provider", "provider"),
        Index("ix_course_catalog_dimensions", "primary_dimension"),
        {"schema": "feedback"},
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(400), nullable=False)
    provider = Column(String(100), nullable=False)   # NPTEL | SWAYAM | AICTE | UGC | IIT-X
    institution = Column(String(200), nullable=True)  # e.g. IIT Madras
    url = Column(Text, nullable=True)
    description = Column(Text, nullable=False)

    # Duration
    duration_weeks = Column(Integer, nullable=True)
    duration_label = Column(String(50), nullable=True)  # e.g. "8 weeks"

    # Pedagogical targeting
    primary_dimension = Column(String(50), nullable=True)  # clarity|methodology|pacing|...
    secondary_dimensions_json = Column(Text, nullable=True)  # JSON array

    # Level and category
    level = Column(String(20), nullable=True)   # beginner | intermediate | advanced
    category = Column(String(100), nullable=True)  # e.g. "Pedagogy", "Subject Expertise"

    # Outcome text (used in recommendations)
    learning_outcomes_json = Column(Text, nullable=True)  # JSON array of outcomes

    # Metadata
    is_active = Column(Boolean, default=True)
    last_verified = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    # Relationship to embeddings
    embedding = relationship("CourseEmbedding", back_populates="course", uselist=False, cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<CourseCatalogEntry title={self.title[:40]} provider={self.provider}>"


class CourseEmbedding(Base):
    """
    pgvector embedding for each course description.
    Used by the RAG engine for semantic similarity search.
    Falls back to a stored JSON array if pgvector not available.
    """
    __tablename__ = "course_embeddings"
    __table_args__ = {"schema": "feedback"}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    course_id = Column(
        String(36),
        ForeignKey("feedback.course_catalog.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    # Embedding stored as JSON array (fallback when pgvector unavailable)
    embedding_json = Column(Text, nullable=False)

    # Embedding model used (for cache invalidation)
    model_name = Column(String(100), nullable=False, default="tfidf-lightweight")
    embedding_dim = Column(Integer, nullable=False, default=768)

    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    course = relationship("CourseCatalogEntry", back_populates="embedding")
