import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from local_ai.infrastructure.observability.metrics import INFLIGHT

log = logging.getLogger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        trace_id = request.headers.get("x-trace-id", uuid.uuid4().hex)
        request.state.trace_id = trace_id
        INFLIGHT.inc()
        start = time.time()
        try:
            response = await call_next(request)
        finally:
            INFLIGHT.dec()
        latency = (time.time() - start) * 1000
        response.headers["x-trace-id"] = trace_id
        response.headers["x-latency-ms"] = f"{latency:.1f}"
        log.info("http %s %s %s %.1fms", request.method, request.url.path, response.status_code, latency)
        return response