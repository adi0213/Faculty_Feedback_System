"""
NLP pipeline orchestrator.
Runs all AI modules on a single FeedbackRecord and persists results.
Designed to be called from the async task worker.
"""
import json
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.absa import analyze_aspects
from app.ai.duplicate_detector import detect_duplicates
from app.ai.sentiment import analyze_sentiment
from app.ai.spam_detector import detect_spam
from app.ai.topic_extractor import extract_topics
from app.models.feedback import FeedbackRecord

logger = logging.getLogger(__name__)


async def process_feedback_record(db: AsyncSession, feedback_id: str) -> bool:
    """
    Full NLP pipeline for one FeedbackRecord.
    Returns True on success, False on failure (record stays queued for retry).
    """
    result = await db.execute(
        select(FeedbackRecord).where(FeedbackRecord.id == feedback_id)
    )
    record = result.scalar_one_or_none()
    if not record:
        logger.error("NLP pipeline: feedback record %s not found", feedback_id)
        return False

    try:
        scores: dict[str, int] = json.loads(record.scores_json) if record.scores_json else {}
        comment = record.comment_raw or ""

        # ── 1. Spam detection ──────────────────────────────────────────────
        spam_result = detect_spam(scores, comment or None)
        record.is_spam = spam_result.is_spam
        record.is_constructive = spam_result.is_constructive

        # ── 2. Sentiment analysis ──────────────────────────────────────────
        if comment and not spam_result.is_spam:
            sentiment = analyze_sentiment(comment)
            record.sentiment_score = sentiment.score
            record.sentiment_label = sentiment.label
            record.comment_language = sentiment.language

            # ── 3. Aspect-based sentiment ──────────────────────────────────
            absa = analyze_aspects(comment)
            record.absa_scores_json = json.dumps(absa.dimension_scores)
            record.flagged_dimensions_json = json.dumps(absa.flagged_dimensions)

            # ── 4. Topic extraction ────────────────────────────────────────
            topics = extract_topics(comment, max_topics=3)
            record.topics_json = json.dumps(topics.topics)

            # ── 5. Duplicate detection ─────────────────────────────────────
            existing_result = await db.execute(
                select(FeedbackRecord.id, FeedbackRecord.comment_raw).where(
                    FeedbackRecord.faculty_profile_id == record.faculty_profile_id,
                    FeedbackRecord.term == record.term,
                    FeedbackRecord.id != record.id,
                    FeedbackRecord.comment_raw.isnot(None),
                    FeedbackRecord.is_spam == False,
                )
            )
            existing_comments = [
                (row.id, row.comment_raw)
                for row in existing_result.fetchall()
                if row.comment_raw
            ]
            dup = detect_duplicates(comment, existing_comments)
            record.is_duplicate = dup.is_duplicate
            record.duplicate_of_id = dup.similar_to

        # ── Mark processed ─────────────────────────────────────────────────
        record.nlp_processed = True
        record.nlp_processed_at = datetime.now(timezone.utc)
        db.add(record)

        logger.info(
            "nlp_processed feedback=%s spam=%s sentiment=%s topics=%s",
            feedback_id, record.is_spam, record.sentiment_label,
            record.topics_json,
        )
        return True

    except Exception as e:
        logger.exception("NLP pipeline failed for feedback %s: %s", feedback_id, e)
        return False
