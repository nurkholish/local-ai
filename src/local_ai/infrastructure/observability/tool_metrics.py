from prometheus_client import Counter, Histogram

TOOL_DURATION = Histogram(
    "agent_tool_duration_seconds",
    "Tool execution duration",
    ["tool"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1, 5, 10, 30],
)
TOOL_ERRORS = Counter("agent_tool_errors_total", "Tool errors", ["tool", "error_type"])
TOOL_BLOCKED = Counter("agent_tool_blocked_total", "Tool calls blocked", ["tool", "reason"])
PII_REDACTIONS = Counter("agent_pii_redactions_total", "PII redactions", ["pattern"])
CIRCUIT_STATE = Counter("agent_circuit_state_total", "Circuit state changes", ["breaker", "state"])
COST_USD = Histogram("agent_request_cost_usd", "Cost per request", buckets=[0.0001, 0.001, 0.01, 0.05, 0.1, 0.5, 1.0])
DEDUP_HITS = Counter("agent_dedup_hits_total", "In-flight dedup hits")