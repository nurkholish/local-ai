from prometheus_client import Counter, Gauge, Histogram

AGENT_REQUESTS = Counter("agent_requests_total", "Total agent requests", ["route", "status"])
AGENT_LATENCY = Histogram("agent_latency_seconds", "Agent latency", buckets=[0.1, 0.5, 1, 2, 5, 10, 30, 60])
AGENT_STEPS = Histogram("agent_steps_per_request", "Steps per request", buckets=[1, 2, 3, 4, 5, 8, 12])
TOOL_CALLS = Counter("agent_tool_calls_total", "Tool calls", ["tool"])
GUARDRAIL_BLOCKS = Counter("agent_guardrail_blocks_total", "Guardrail blocks", ["layer", "reason"])
CHECK_FAILS = Counter("agent_check_fails_total", "Check fails", ["name", "severity"])
LLM_TOKENS = Counter("agent_llm_tokens_total", "LLM tokens", ["provider", "direction"])
INFLIGHT = Gauge("agent_inflight_requests", "In-flight requests")