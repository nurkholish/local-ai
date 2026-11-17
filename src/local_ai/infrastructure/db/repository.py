import logging

from sqlalchemy import select
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from local_ai.config import Settings
from local_ai.infrastructure.db.models import Base, Conversation

log = logging.getLogger(__name__)


class ConversationRepository:
    def __init__(self, settings: Settings):
        self._engine = create_async_engine(settings.database_url, echo=False, pool_pre_ping=True)
        self._session = async_sessionmaker(self._engine, class_=AsyncSession, expire_on_commit=False)

    async def init_schema(self) -> None:
        try:
            async with self._engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
        except (ProgrammingError, Exception) as e:
            if "already exists" in str(e).lower():
                log.info("schema already exists")
                return
            raise

    async def save(self, trace_id: str, user_key: str, user_message: str, answer: str, route: str) -> None:
        try:
            async with self._session() as s:
                s.add(Conversation(
                    trace_id=trace_id, user_key=user_key,
                    user_message=user_message, answer=answer, route=route,
                ))
                await s.commit()
        except Exception:
            log.exception("persist failed")

    async def list_by_user(self, user_key: str, limit: int = 50):
        try:
            async with self._session() as s:
                r = await s.execute(
                    select(Conversation).where(Conversation.user_key == user_key)
                    .order_by(Conversation.created_at.desc()).limit(limit)
                )
                return r.scalars().all()
        except Exception:
            log.exception("list failed")
            return []