import logging
from typing import Protocol

import httpx

from local_ai.config import Settings

log = logging.getLogger(__name__)


class Embedder(Protocol):
    async def embed(self, texts: list[str]) -> list[list[float]]: ...
    @property
    def dim(self) -> int: ...


class TEIEmbedder:
    def __init__(self, settings: Settings):
        self._url = settings.embedding_url
        self._client = httpx.AsyncClient(timeout=30)
        self._dim = 1024

    @property
    def dim(self) -> int:
        return self._dim

    async def embed(self, texts: list[str]) -> list[list[float]]:
        r = await self._client.post(f"{self._url}/embed", json={"inputs": texts})
        r.raise_for_status()
        return r.json()


class DummyEmbedder:
    @property
    def dim(self) -> int:
        return 1024

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.0] * 1024 for _ in texts]


def make_embedder(settings: Settings) -> Embedder:
    try:
        e = TEIEmbedder(settings)
        log.info("using TEI embedder")
        return e
    except Exception:
        log.warning("TEI unavailable — DummyEmbedder")
        return DummyEmbedder()