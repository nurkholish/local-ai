import logging

from fastapi import APIRouter, Request

log = logging.getLogger(__name__)
router = APIRouter()


@router.get("/v1/conversations/{user_key}")
async def list_conversations(user_key: str, request: Request, limit: int = 50):
    repo = request.app.state.repo
    if not repo:
        return {"items": []}
    try:
        rows = await repo.list_by_user(user_key, limit)
        return {"items": [
            {"trace_id": r.trace_id, "user_key": r.user_key, "user_message": r.user_message,
             "answer": r.answer, "route": r.route, "created_at": r.created_at.isoformat()}
            for r in rows
        ]}
    except Exception:
        log.exception("list failed")
        return {"items": []}