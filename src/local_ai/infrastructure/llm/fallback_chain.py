import logging
from dataclasses import dataclass
from typing import AsyncIterator, Any

from openai import AsyncOpenAI

log = logging.getLogger(__name__)


@dataclass
class ModelProvider:
    name: str
    client: AsyncOpenAI
    model: str


class FallbackChain:
    def __init__(self, providers: list[ModelProvider]):
        if not providers:
            raise ValueError("at least one provider required")
        self.providers = providers

    async def complete(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        extra_kwargs: dict | None = None,
    ) -> Any:
        last_err: Exception | None = None
        for p in self.providers:
            try:
                log.info("trying %s (model=%s)", p.name, p.model)
                kwargs = {**(extra_kwargs or {})}
                if tools:
                    kwargs["tools"] = tools
                return await p.client.chat.completions.create(
                    model=p.model, messages=messages, **kwargs
                )
            except Exception as e:
                log.warning("provider %s failed: %s", p.name, type(e).__name__)
                last_err = e
                continue
        raise RuntimeError(f"all providers failed: {last_err}")

    async def stream(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        extra_kwargs: dict | None = None,
    ) -> AsyncIterator[str]:
        last_err: Exception | None = None
        for p in self.providers:
            try:
                kwargs = {**(extra_kwargs or {}), "stream": True}
                if tools:
                    kwargs["tools"] = tools
                stream = await p.client.chat.completions.create(
                    model=p.model, messages=messages, **kwargs
                )
                async for chunk in stream:
                    delta = chunk.choices[0].delta.content
                    if delta:
                        yield delta
                return
            except Exception as e:
                log.warning("stream %s failed: %s", p.name, type(e).__name__)
                last_err = e
        raise RuntimeError(f"all providers failed (stream): {last_err}")