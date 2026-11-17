import logging
from dataclasses import dataclass, field

from local_ai.domain.ports import RetrieverPort

log = logging.getLogger(__name__)


@dataclass
class ContextBundle:
    system: str
    history: list[dict] = field(default_factory=list)
    rag: list[str] = field(default_factory=list)
    user: str = ""

    def to_messages(self) -> list[dict]:
        parts = [self.system]
        if self.rag:
            parts.append("## Retrieved context\n" + "\n---\n".join(self.rag))
        return [
            {"role": "system", "content": "\n\n".join(parts)},
            *self.history,
            {"role": "user", "content": self.user},
        ]


class ContextBuilder:
    def __init__(
        self,
        retriever: RetrieverPort | None = None,
        max_history_turns: int = 10,
        max_rag_chunks: int = 5,
    ):
        self.retriever = retriever
        self.max_history_turns = max_history_turns
        self.max_rag_chunks = max_rag_chunks

    async def build(self, user_input: str, history: list[dict] | None, system: str) -> ContextBundle:
        hist = (history or [])[-self.max_history_turns:]
        rag: list[str] = []
        if self.retriever:
            try:
                docs = await self.retriever.retrieve(user_input, k=self.max_rag_chunks)
                rag = [d.text if hasattr(d, "text") else d["text"] for d in docs]
            except Exception:
                log.exception("retriever failed")
        return ContextBundle(system=system, history=hist, rag=rag, user=user_input)