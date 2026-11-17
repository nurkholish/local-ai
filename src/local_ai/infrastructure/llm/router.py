import asyncio
import logging
from typing import Any, AsyncIterator

from openai import AsyncOpenAI

from local_ai.application.circuit_breaker import get_circuit_breakers
from local_ai.application.retry_budget import RetryBudget
from local_ai.config import Settings
from local_ai.infrastructure.llm.cost_tracker import CostAccumulator
from local_ai.infrastructure.llm.fallback_chain import FallbackChain, ModelProvider
from local_ai.infrastructure.observability.tool_metrics import CIRCUIT_STATE

log = logging.getLogger(__name__)


class LLMRouter:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._local_router = AsyncOpenAI(base_url=settings.vllm_router_url, api_key="local", timeout=settings.llm_timeout_s)
        self._local_main = AsyncOpenAI(base_url=settings.vllm_main_url, api_key="local", timeout=settings.llm_timeout_s)
        self._frontier = (
            AsyncOpenAI(api_key=settings.openai_api_key, timeout=settings.llm_timeout_s)
            if settings.openai_api_key else None
        )
        self._cbs = get_circuit_breakers()

    async def classify(self, text: str) -> str:
        if self.settings.llm_route_mode == "frontier":
            return "complex"
        if self.settings.llm_route_mode == "local" or not self.settings.vllm_enabled:
            return "simple"
        try:
            cb = self._cbs.get("classifier")
            if cb.is_open():
                return "simple"
            r = await self._local_router.chat.completions.create(
                model=self.settings.llm_route_classifier_model,
                messages=[{"role": "user", "content": f"Classify: simple|complex\n\n{text}\n\nAnswer:"}],
                max_tokens=5,
                temperature=0,
                extra_body={"cache_prompt": True},
            )
            cb.on_success()
            return (r.choices[0].message.content or "").strip().lower() or "simple"
        except Exception:
            self._cbs.get("classifier").on_failure()
            return "simple"

    def _build_chain(self, route: str) -> FallbackChain:
        providers: list[ModelProvider] = []
        if self.settings.vllm_enabled:
            providers.append(ModelProvider("local", self._local_main, self.settings.llm_route_local_model))
        if route == "complex" and self._frontier:
            providers.append(ModelProvider("frontier", self._frontier, self.settings.llm_route_frontier_model))
        elif self._frontier and not self.settings.vllm_enabled:
            providers.append(ModelProvider("frontier", self._frontier, self.settings.llm_route_frontier_model))
        if not providers:
            raise RuntimeError("No LLM provider available")
        return FallbackChain(providers)

    def _build_kwargs(self) -> dict:
        kwargs: dict[str, Any] = {
            "temperature": 0.2,
            "max_tokens": self.settings.llm_max_output_tokens,
        }
        if self.settings.llm_cache_prompt:
            kwargs["extra_body"] = {"cache_prompt": True}
        return kwargs

    async def complete(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        budget: RetryBudget | None = None,
        cost: CostAccumulator | None = None,
    ) -> Any:
        route = await self.classify(messages[-1].get("content", ""))
        chain = self._build_chain(route)
        cb = self._cbs.get(f"llm:{route}")

        if cb.is_open():
            CIRCUIT_STATE.labels(breaker=f"llm:{route}", state="open").inc()
            raise RuntimeError(f"LLM circuit OPEN for route={route}")

        budget = budget or RetryBudget(self.settings.retry_budget_s, self.settings.retry_max_attempts)
        delay = 1.0
        last_err: Exception | None = None

        while budget.can_retry():
            budget.consume()
            try:
                resp = await chain.complete(messages, tools=tools, extra_kwargs=self._build_kwargs())
                cb.on_success()
                if cost is not None and hasattr(resp, "usage") and resp.usage:
                    cost.record(resp.usage.model_dump(), chain.providers[0].model)
                return resp
            except Exception as e:
                last_err = e
                log.warning("LLM attempt %d failed: %s", budget.attempts, type(e).__name__)
                if budget.can_retry(min_needed_s=delay):
                    await asyncio.sleep(delay)
                    delay = min(delay * 2, 8.0)
                else:
                    break

        cb.on_failure()
        CIRCUIT_STATE.labels(breaker=f"llm:{route}", state="failure").inc()
        raise RuntimeError(f"LLM failed after {budget.attempts} attempts: {last_err}")

    async def stream(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
    ) -> AsyncIterator[str]:
        route = await self.classify(messages[-1].get("content", ""))
        chain = self._build_chain(route)
        async for token in chain.stream(messages, tools=tools, extra_kwargs=self._build_kwargs()):
            yield token