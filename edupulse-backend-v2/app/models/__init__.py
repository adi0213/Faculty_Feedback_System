"""
Models package — import all models here so Alembic and SQLAlchemy can discover them.
"""
from app.models.user import User
from app.models.faculty import FacultyProfile
from app.models.feedback import FeedbackRecord, SubmissionRecord
from app.models.token import PseudoToken
from app.models.course_catalog import CourseCatalogEntry, CourseEmbedding
from app.models.roadmap import CourseRecommendation, FacultyRoadmap
from app.models.audit_log import AuditLog

__all__ = [
    "User",
    "FacultyProfile",
    "FeedbackRecord",
    "SubmissionRecord",
    "PseudoToken",
    "CourseCatalogEntry",
    "CourseEmbedding",
    "CourseRecommendation",
    "FacultyRoadmap",
    "AuditLog",
]
