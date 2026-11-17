import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_client import make_asgi_app

from local_ai.application.rag.embedder import make_embedder
from local_ai.application.rag.retriever import RAGRetriever
from local_ai.application.use_cases.run_agent import RunAgentUseCase
from local_ai.config import get_settings
from local_ai.infrastructure.cache.semantic_cache import SemanticCache
from local_ai.infrastructure.db.repository import ConversationRepository
from local_ai.infrastructure.db.vectors import VectorStore
from local_ai.infrastructure.llm.router import LLMRouter
from local_ai.infrastructure.observability.logging import setup_logging
from local_ai.infrastructure.observability.tracing import init_tracing, instrument_fastapi
from local_ai.infrastructure.rate_limit.redis_limiter import RedisRateLimiter
from local_ai.interface.http.middleware import RequestContextMiddleware
from local_ai.interface.http.routes import chat, conversations, documents

log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    s = get_settings()
    setup_logging(s.log_level, s.log_json)

    if s.otel_enabled:
        try:
            init_tracing(s.otel_exporter_otlp_endpoint, s.otel_service_name)
        except Exception:
            log.exception("otel init failed")

    llm = LLMRouter(s)
    app.state.llm = llm

    embedder = make_embedder(s)
    app.state.embedder = embedder

    try:
        vs = VectorStore(s)
        await vs.init_schema(dim=embedder.dim)
        app.state.vector_store = vs
        app.state.retriever = RAGRetriever(embedder, vs._session)
    except Exception:
        log.exception("vector store init failed")
        app.state.vector_store = None
        app.state.retriever = None

    app.state.cache = SemanticCache(s, embedder)
    app.state.rate_limiter = RedisRateLimiter(s.redis_url, s.rate_limit_per_min)

    try:
        repo = ConversationRepository(s)
        await repo.init_schema()
        app.state.repo = repo
    except Exception:
        log.exception("db init failed")
        app.state.repo = None

    app.state.use_case = RunAgentUseCase(
        llm=llm, settings=s,
        retriever=app.state.retriever,
        cache=app.state.cache,
        rate_limiter=app.state.rate_limiter,
        conversations=app.state.repo,
    )

    log.info("Agent ready env=%s route_mode=%s cb=%s pii=%s dedup=%s",
             s.env, s.llm_route_mode, s.cb_failure_threshold,
             s.pii_redaction_enabled, s.dedup_enabled)
    yield
    log.info("Shutdown")


def create_app() -> FastAPI:
    app = FastAPI(title="local-ai", lifespan=lifespan)
    app.add_middleware(RequestContextMiddleware)
    app.include_router(chat.router)
    app.include_router(conversations.router)
    app.include_router(documents.router)
    app.mount("/metrics", make_asgi_app())
    try:
        instrument_fastapi(app)
    except Exception:
        pass
    return app