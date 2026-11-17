import logging
from dataclasses import dataclass

from sqlalchemy import text

from local_ai.application.rag.embedder import Embedder

log = logging.getLogger(__name__)


@dataclass
class RetrievedDoc:
    id: int
    text: str
    score: float
    metadata: dict


class RAGRetriever:
    def __init__(self, embedder: Embedder, session_factory):
        self.embedder = embedder
        self._session = session_factory

    async def retrieve(self, query: str, k: int = 5, min_score: float = 0.3) -> list[RetrievedDoc]:
        try:
            [vec] = await self.embedder.embed([query])
            vec_str = "[" + ",".join(str(v) for v in vec) + "]"
            async with self._session() as s:
                result = await s.execute(
                    text("""
                        SELECT id, text, metadata,
                               1 - (embedding <=> CAST(:vec AS vector)) AS score
                        FROM documents
                        ORDER BY embedding <=> CAST(:vec AS vector)
                        LIMIT :k
                    """),
                    {"vec": vec_str, "k": k},
                )
                return [
                    RetrievedDoc(id=row[0], text=row[1], score=float(row[3]), metadata=row[2] or {})
                    for row in result.fetchall()
                    if float(row[3]) >= min_score
                ]
        except Exception:
            log.exception("RAG retrieve failed")
            return []