import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from local_ai.config import Settings

log = logging.getLogger(__name__)


class VectorStore:
    def __init__(self, settings: Settings):
        self._engine = create_async_engine(settings.database_url, pool_pre_ping=True)
        self._session = async_sessionmaker(self._engine, expire_on_commit=False)

    async def init_schema(self, dim: int = 1024) -> None:
        async with self._engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            await conn.execute(text(f"""
                CREATE TABLE IF NOT EXISTS documents (
                    id BIGSERIAL PRIMARY KEY,
                    doc_id TEXT,
                    text TEXT NOT NULL,
                    metadata JSONB,
                    embedding vector({dim}),
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """))
        log.info("vector schema initialized (dim=%d)", dim)

    async def insert(self, doc_id: str, chunks: list[str], embeddings: list[list[float]], metadata: dict | None = None) -> int:
        async with self._session() as s:
            for chunk, emb in zip(chunks, embeddings, strict=True):
                vec_str = "[" + ",".join(str(v) for v in emb) + "]"
                await s.execute(
                    text("""
                        INSERT INTO documents (doc_id, text, metadata, embedding)
                        VALUES (:doc_id, :text, CAST(:meta AS jsonb), CAST(:emb AS vector))
                    """),
                    {"doc_id": doc_id, "text": chunk, "meta": str(metadata or {}).replace("'", '"'), "emb": vec_str},
                )
            await s.commit()
        return len(chunks)