import json
import logging
from dataclasses import dataclass
from typing import AsyncIterator

log = logging.getLogger(__name__)


@dataclass
class StreamEvent:
    type: str
    data: dict

    def to_dict(self) -> dict:
        """Return dict for EventSourceResponse — let library format SSE."""
        return {"event": self.type, "data": json.dumps(self.data)}


async def stream_chat(llm_stream: AsyncIterator[str], trace_id: str) -> AsyncIterator[StreamEvent]:
    yield StreamEvent(type="start", data={"trace_id": trace_id, "type": "start"})
    try:
        async for token in llm_stream:
            yield StreamEvent(type="token", data={"content": token, "type": "token"})
        yield StreamEvent(type="done", data={"trace_id": trace_id, "type": "done"})
    except Exception as e:
        log.exception("stream error")
        yield StreamEvent(type="error", data={"error": str(e), "type": "error"})