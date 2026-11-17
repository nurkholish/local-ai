import hashlib
import json
import logging

import redis.asyncio as redis

from local_ai.application.rag.embedder import Embedder
from local_ai.config import Settings

log = logging.getLogger(__name__)


class SemanticCache:
    def __init__(self, settings: Settings, embedder: Embedder):
        self._redis = redis.from_url(settings.redis_url, decode_responses=True)
        self._embedder = embedder
        self._prefix = "semantic_cache:"
        self._enabled = True

    async def get(self, query: str) -> str | None:
        if not self._enabled:
            return None
        try:
            result = await self._embedder.embed([query])
            if not result or not result[0]:
                return None
            vec = result[0]
            if all(v == 0 for v in vec):
                log.debug("cache disabled: dummy embedder")
                self._enabled = False
                return None
            key = f"{self._prefix}{self._hash(vec)}"
            cached = await self._redis.get(key)
            if cached:
                log.info("semantic cache hit")
                return json.loads(cached)["answer"]
            return None
        except Exception as e:
            log.warning("cache get failed: %s", type(e).__name__)
            return None

    async def set(self, query: str, answer: str, ttl_s: int = 3600) -> None:
        if not self._enabled:
            return
        try:
            result = await self._embedder.embed([query])
            if not result or not result[0]:
                return
            vec = result[0]
            if all(v == 0 for v in vec):
                self._enabled = False
                return
            key = f"{self._prefix}{self._hash(vec)}"
            await self._redis.set(key, json.dumps({"query": query, "answer": answer}), ex=ttl_s)
        except Exception as e:
            log.warning("cache set failed: %s", type(e).__name__)

    @staticmethod
    def _hash(vec: list[float]) -> str:
        rounded = [round(v, 3) for v in vec]
        return hashlib.sha256(str(rounded).encode()).hexdigest()[:32]