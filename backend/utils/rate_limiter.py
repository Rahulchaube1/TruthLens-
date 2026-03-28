"""Simple Redis-backed sliding-window rate limiter."""
import logging
import os
import time
from typing import Optional

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

try:
    import redis.asyncio as aioredis
    _redis: Optional[aioredis.Redis] = None

    async def get_redis() -> aioredis.Redis:
        global _redis
        if _redis is None:
            _redis = aioredis.from_url(REDIS_URL, decode_responses=True)
        return _redis

    async def check_rate_limit(identifier: str, limit: int = 60, window_seconds: int = 60) -> bool:
        """Return True if request is allowed, False if rate-limited."""
        try:
            r = await get_redis()
            key = f"rl:{identifier}"
            now = time.time()
            pipe = r.pipeline()
            pipe.zremrangebyscore(key, 0, now - window_seconds)
            pipe.zadd(key, {str(now): now})
            pipe.zcard(key)
            pipe.expire(key, window_seconds * 2)
            results = await pipe.execute()
            count = results[2]
            return count <= limit
        except Exception as exc:
            logger.warning("Rate limiter error (allowing request): %s", exc)
            return True  # Fail open

except ImportError:
    async def check_rate_limit(identifier: str, limit: int = 60, window_seconds: int = 60) -> bool:
        return True
