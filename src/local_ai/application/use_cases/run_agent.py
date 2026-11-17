import json
import logging
import time
import uuid

from local_ai.application.checks import OutputChecks
from local_ai.application.context_builder import ContextBuilder
from local_ai.application.deduplicator import InFlightDeduplicator
from local_ai.application.guardrails import InputGuard, ToolGuard
from local_ai.application.pii_redactor import PIIRedactor
from local_ai.application.prompts.registry import get_prompt_registry
from local_ai.application.retry_budget import RetryBudget
from local_ai.application.tools_registry import TOOL_IMPL, TOOL_SCHEMAS
from local_ai.config import Settings
from local_ai.domain.entities import AgentRequest, AgentResponse, ToolCall
from local_ai.domain.ports import LLMPort
from local_ai.infrastructure.llm.cost_tracker import CostAccumulator
from local_ai.infrastructure.observability.metrics import (
    AGENT_LATENCY, AGENT_REQUESTS, CHECK_FAILS, GUARDRAIL_BLOCKS, TOOL_CALLS,
)
from local_ai.infrastructure.observability.tool_metrics import COST_USD, PII_REDACTIONS, TOOL_BLOCKED

log = logging.getLogger(__name__)


class RunAgentUseCase:
    def __init__(
        self,
        llm: LLMPort,
        settings: Settings,
        retriever=None,
        cache=None,
        rate_limiter=None,
        conversations=None,
    ):
        self.llm = llm
        self.settings = settings
        self.cache = cache
        self.rate_limiter = rate_limiter
        self.conversations = conversations
        self.prompts = get_prompt_registry()
        self.ctx_builder = ContextBuilder(retriever=retriever, max_rag_chunks=settings.max_rag_chunks)
        self.input_guard = InputGuard()
        self.tool_guard = ToolGuard(allowed_tools=set(TOOL_IMPL), max_calls_per_turn=5)
        self.checks = OutputChecks()
        self.pii = PIIRedactor(
            enabled=settings.pii_redaction_enabled,
            redact_on_output=settings.pii_redaction_on_output,
        )
        self.dedup = InFlightDeduplicator() if settings.dedup_enabled else None

    async def execute(self, req: AgentRequest) -> AgentResponse:
        if self.dedup:
            return await self.dedup.run_or_wait(req.message, req.user_key, lambda: self._execute(req))
        return await self._execute(req)

    async def _execute(self, req: AgentRequest) -> AgentResponse:
        trace_id = uuid.uuid4().hex
        start = time.time()
        resp = AgentResponse(answer="", trace_id=trace_id)
        cost = CostAccumulator()
        budget = RetryBudget(self.settings.retry_budget_s, self.settings.retry_max_attempts)

        # Rate limit
        if self.rate_limiter:
            ok, why = await self.rate_limiter.check(req.user_key)
            if not ok:
                GUARDRAIL_BLOCKS.labels(layer="policy", reason=why).inc()
                resp.answer, resp.blocked_by = why, "policy_guard"
                return resp

        # PII redaction
        user_message = self.pii.redact(req.message)
        if user_message != req.message:
            for label in ["email", "phone_id", "nik", "credit_card", "api_key_sk", "api_key_ghp"]:
                if f"[REDACTED_{label.upper()}]" in user_message:
                    PII_REDACTIONS.labels(pattern=label).inc()

        # Cache
        if self.cache:
            cached = await self.cache.get(req.message)
            if cached:
                resp.answer = cached
                resp.latency_ms = (time.time() - start) * 1000
                return resp

        # Input guard
        ok, why = self.input_guard.check(user_message)
        if not ok:
            GUARDRAIL_BLOCKS.labels(layer="input", reason=why).inc()
            resp.answer, resp.blocked_by = why, "input_guard"
            return resp

        # Context
        system_prompt = self.prompts.get("system", "default")
        ctx = await self.ctx_builder.build(user_message, req.history, system_prompt)
        messages = ctx.to_messages()

        # Loop
        tool_results: list[dict] = []
        final_content = ""
        for step in range(self.settings.max_agent_steps):
            try:
                llm_resp = await self.llm.complete(messages, tools=TOOL_SCHEMAS, budget=budget, cost=cost)
            except Exception:
                log.exception("llm failed at step %d", step)
                resp.answer = f"Service temporarily unavailable. Please retry. (trace: {trace_id[:8]})"
                resp.blocked_by = "llm_unavailable"
                return resp

            msg = llm_resp.choices[0].message
            messages.append(msg.model_dump(exclude_none=True))
            if not msg.tool_calls:
                final_content = msg.content or ""
                break

            self.tool_guard.reset_turn()
            for tc in msg.tool_calls:
                name = tc.function.name
                args: dict = {}
                try:
                    args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    result = f"[tool:{name} invalid JSON args]"
                else:
                    allowed, why = self.tool_guard.check(name, args)
                    if not allowed:
                        TOOL_BLOCKED.labels(tool=name, reason=why).inc()
                        GUARDRAIL_BLOCKS.labels(layer="tool", reason=why).inc()
                        result = f"[tool:{name} blocked — {why}]"
                    else:
                        fn = TOOL_IMPL.get(name)
                        TOOL_CALLS.labels(tool=name).inc()
                        result = await fn(**args) if fn else f"[tool:{name} not found]"

                tool_results.append({"tool": name, "result": str(result)[:500]})
                resp.steps.append(
                    ToolCall(
                        name=name, args=args, result=str(result)[:200],
                        blocked="blocked" in str(result).lower(),
                    )
                )
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": str(result)})

            # Early return for calculator
            if (
                self.settings.llm_early_return_calculator
                and len(msg.tool_calls) == 1
                and msg.tool_calls[0].function.name == "calculator"
                and not resp.steps[-1].blocked
            ):
                final_content = f"The result is {resp.steps[-1].result}."
                log.info("early return: calculator fast-path")
                break
        else:
            try:
                llm_resp = await self.llm.complete(messages, budget=budget, cost=cost)
                final_content = llm_resp.choices[0].message.content or ""
            except Exception:
                final_content = "Unable to finalize answer within step limit."

        # Output checks
        results = self.checks.run(final_content, {"system_prompt": system_prompt, "tool_results": tool_results})
        passed, _ = self.checks.aggregate(results)
        for r in results:
            resp.checks.append({"name": r.name, "passed": r.passed})
            if not r.passed:
                CHECK_FAILS.labels(name=r.name, severity=r.severity.value).inc()

        # PII on output
        answer = self.pii.redact(final_content) if self.settings.pii_redaction_on_output else final_content
        resp.answer = answer if passed else "I cannot provide a safe answer to this request."
        if not passed:
            resp.blocked_by = "output_checks"

        resp.latency_ms = (time.time() - start) * 1000

        # Persist + cache
        if self.conversations and passed:
            try:
                await self.conversations.save(trace_id, req.user_key, req.message, resp.answer, "auto")
            except Exception:
                log.exception("persist failed")
        if self.cache and passed:
            await self.cache.set(req.message, resp.answer)

        # Metrics
        AGENT_REQUESTS.labels(route="auto", status="ok").inc()
        AGENT_LATENCY.observe(resp.latency_ms / 1000)
        COST_USD.observe(cost.cost_usd)

        resp.cost = cost.to_dict()
        return resp