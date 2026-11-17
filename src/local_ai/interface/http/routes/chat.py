import json
import logging
import uuid

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from local_ai.application.streaming import stream_chat
from local_ai.application.use_cases.run_agent import RunAgentUseCase
from local_ai.domain.entities import AgentRequest

log = logging.getLogger(__name__)
router = APIRouter()


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=20000)
    history: list[dict] | None = None
    user_key: str = "anon"


class ChatOut(BaseModel):
    answer: str
    route: str = ""
    trace_id: str
    latency_ms: float
    blocked_by: str | None = None
    steps: list[dict] = []
    checks: list[dict] = []
    cost: dict = {}


@router.get("/healthz")
async def healthz():
    return {"status": "ok"}


@router.get("/readyz")
async def readyz():
    return {"status": "ready"}


@router.post("/v1/chat", response_model=ChatOut)
async def chat(req: ChatIn, request: Request):
    uc: RunAgentUseCase = request.app.state.use_case
    try:
        result = await uc.execute(AgentRequest(message=req.message, user_key=req.user_key, history=req.history or []))
    except Exception as e:
        log.exception("chat failed")
        raise HTTPException(500, "Agent failure") from e
    return ChatOut(
        answer=result.answer,
        route=result.route,
        trace_id=result.trace_id,
        latency_ms=result.latency_ms,
        blocked_by=result.blocked_by,
        steps=[{"name": s.name, "result": s.result, "blocked": s.blocked} for s in result.steps],
        checks=result.checks,
        cost=result.cost,
    )


@router.post("/v1/chat/stream")
async def chat_stream(req: ChatIn, request: Request):
    uc: RunAgentUseCase = request.app.state.use_case
    trace_id = uuid.uuid4().hex

    async def gen():
        try:
            if uc.rate_limiter:
                ok, why = await uc.rate_limiter.check(req.user_key)
                if not ok:
                    yield {"event": "error", "data": json.dumps({"error": why, "type": "error"})}
                    return
            system_prompt = uc.prompts.get("system", "default")
            ctx = await uc.ctx_builder.build(req.message, req.history, system_prompt)
            messages = ctx.to_messages()
            async for event in stream_chat(uc.llm.stream(messages), trace_id):
                yield event.to_dict()
        except Exception as e:
            log.exception("stream failed")
            yield {"event": "error", "data": json.dumps({"error": str(e), "type": "error"})}

    return EventSourceResponse(gen())