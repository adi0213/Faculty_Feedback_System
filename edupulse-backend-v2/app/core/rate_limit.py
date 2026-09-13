"""
Redis-backed sliding window rate limiter.
Falls back to a simple in-process counter if Redis is unavailable.
"""
import logging
import time
from collections import defaultdict
from functools import wraps
from typing import Callable

from fastapi import Request

from app.config import get_settings
from app.core.exceptions import RateLimitError

logger = logging.getLogger(__name__)
settings = get_settings()

# ── Redis connection (lazy, module-level singleton) ───────────────────────────
_redis_client = None


def _get_redis():
    global _redis_client
    if _redis_client is None:
        try:
            import redis.asyncio as aioredis
            _redis_client = aioredis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
            )
        except Exception as e:
            logger.warning("Redis unavailable, using in-process rate limiter: %s", e)
            _redis_client = None
    return _redis_client


# ── In-process fallback ───────────────────────────────────────────────────────
_in_memory_buckets: dict[str, list[float]] = defaultdict(list)


async def _check_in_process(key: str, limit: int, window_seconds: int) -> bool:
    """Simple in-memory sliding window. Not suitable for multi-process deployments."""
    now = time.time()
    bucket = _in_memory_buckets[key]
    # Remove expired entries
    _in_memory_buckets[key] = [t for t in bucket if now - t < window_seconds]
    if len(_in_memory_buckets[key]) >= limit:
        return False
    _in_memory_buckets[key].append(now)
    return True


async def _check_redis(key: str, limit: int, window_seconds: int) -> bool:
    """Redis sliding window using sorted sets."""
    r = _get_redis()
    if r is None:
        return await _check_in_process(key, limit, window_seconds)
    try:
        now = time.time()
        pipe = r.pipeline()
        pipe.zremrangebyscore(key, 0, now - window_seconds)
        pipe.zadd(key, {str(now): now})
        pipe.zcard(key)
        pipe.expire(key, window_seconds)
        results = await pipe.execute()
        count = results[2]
        return count <= limit
    except Exception as e:
        logger.warning("Redis rate limit check failed, falling back: %s", e)
        return await _check_in_process(key, limit, window_seconds)


async def check_rate_limit(
    request: Request,
    limit: int,
    window_seconds: int,
    scope: str = "api",
) -> None:
    """
    Check the rate limit for the current request's IP.
    Raises RateLimitError if limit exceeded.
    """
    if settings.app_env == "test":
        return

    ip = request.client.host if request.client else "unknown"
    key = f"rl:{scope}:{ip}"
    allowed = await _check_redis(key, limit, window_seconds)
    if not allowed:
        raise RateLimitError()


# ── Convenience dependency factories ─────────────────────────────────────────
def rate_limit(limit: int, window_seconds: int, scope: str = "api"):
    """FastAPI dependency factory for rate limiting."""
    async def _dep(request: Request):
        await check_rate_limit(request, limit, window_seconds, scope)
    return _dep


feedback_rate_limit = rate_limit(
    limit=settings.rate_limit_feedback_per_hour,
    window_seconds=3600,
    scope="feedback",
)

auth_rate_limit = rate_limit(
    limit=settings.rate_limit_auth_per_minute,
    window_seconds=60,
    scope="auth",
)
