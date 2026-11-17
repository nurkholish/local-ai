import logging
import time

import redis.asyncio as redis

log = logging.getLogger(__name__)


class RedisRateLimiter:
    def __init__(self, redis_url: str, per_minute: int = 60):
        self._redis = redis.from_url(redis_url, decode_responses=True)
        self._limit = per_minute

    async def check(self, user_key: str) -> tuple[bool, str]:
        try:
            window = int(time.time() // 60)
            key = f"rl:{user_key}:{window}"
            n = await self._redis.incr(key)
            if n == 1:
                await self._redis.expire(key, 60)
            if n > self._limit:
                return False, f"rate limit exceeded ({self._limit}/min)"
            return True, ""
        except Exception:
            log.exception("rate limit check failed — allowing")
            return True, ""