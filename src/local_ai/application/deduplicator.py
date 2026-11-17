import asyncio
import hashlib
import logging
from typing import Any, Awaitable, Callable

log = logging.getLogger(__name__)


class InFlightDeduplicator:
    def __init__(self):
        self._inflight: dict[str, asyncio.Future] = {}

    @staticmethod
    def _key(text: str, user_key: str) -> str:
        return hashlib.sha256(f"{user_key}:{text}".encode()).hexdigest()[:16]

    async def run_or_wait(
        self,
        text: str,
        user_key: str,
        fn: Callable[[], Awaitable[Any]],
    ) -> Any:
        key = self._key(text, user_key)
        if key in self._inflight:
            log.info("dedup hit")
            return await self._inflight[key]

        loop = asyncio.get_event_loop()
        fut: asyncio.Future = loop.create_future()
        self._inflight[key] = fut
        try:
            result = await fn()
            if not fut.done():
                fut.set_result(result)
            return result
        except Exception as e:
            if not fut.done():
                fut.set_exception(e)
            raise
        finally:
            self._inflight.pop(key, None)