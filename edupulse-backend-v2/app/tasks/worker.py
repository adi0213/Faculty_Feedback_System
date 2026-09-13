"""
Async task worker using Redis as the queue.
Falls back to synchronous in-process execution when Redis is unavailable.
"""
import asyncio
import json
import logging

logger = logging.getLogger(__name__)

QUEUE_KEY = "edupulse:nlp_queue"
_redis = None


def _get_redis():
    global _redis
    if _redis is None:
        try:
            import redis.asyncio as aioredis
            from app.config import get_settings
            _redis = aioredis.from_url(
                get_settings().redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=2,
            )
        except Exception as e:
            logger.warning("Redis unavailable for task queue: %s", e)
            _redis = None
    return _redis


async def enqueue_nlp_task(feedback_id: str) -> bool:
    """Push a feedback ID onto the NLP processing queue."""
    r = _get_redis()
    if r is None:
        # Fallback: process synchronously inline
        await _process_inline(feedback_id)
        return True
    try:
        await r.rpush(QUEUE_KEY, json.dumps({"feedback_id": feedback_id}))
        logger.debug("Enqueued NLP task for feedback %s", feedback_id)
        return True
    except Exception as e:
        logger.warning("Failed to enqueue task, processing inline: %s", e)
        await _process_inline(feedback_id)
        return True


async def _process_inline(feedback_id: str) -> None:
    """Process a feedback record inline (no Redis). Used as fallback."""
    try:
        from app.db.session import get_db_context
        from app.services.nlp_service import process_feedback_record
        async with get_db_context() as db:
            await process_feedback_record(db, feedback_id)
    except Exception as e:
        logger.exception("Inline NLP processing failed for %s: %s", feedback_id, e)


async def worker_loop(concurrency: int = 4) -> None:
    """
    Continuous worker loop that pulls tasks from Redis and processes them.
    Run this as a separate process: `python -m app.tasks.worker`
    """
    logger.info("NLP worker starting with concurrency=%d", concurrency)
    semaphore = asyncio.Semaphore(concurrency)

    while True:
        r = _get_redis()
        if r is None:
            logger.warning("Worker: Redis not available, sleeping 10s")
            await asyncio.sleep(10)
            continue
        try:
            # Blocking pop with 5s timeout
            item = await r.blpop(QUEUE_KEY, timeout=5)
            if item is None:
                continue
            _, payload = item
            data = json.loads(payload)
            feedback_id = data.get("feedback_id")
            if feedback_id:
                async with semaphore:
                    await _process_inline(feedback_id)
        except Exception as e:
            logger.error("Worker loop error: %s", e)
            await asyncio.sleep(1)


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    asyncio.run(worker_loop())
