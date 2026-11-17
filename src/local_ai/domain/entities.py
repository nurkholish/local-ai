from dataclasses import dataclass, field


@dataclass
class ToolCall:
    name: str
    args: dict
    result: str = ""
    blocked: bool = False
    reason: str = ""


@dataclass
class AgentRequest:
    message: str
    user_key: str = "anon"
    history: list[dict] = field(default_factory=list)


@dataclass
class AgentResponse:
    answer: str
    route: str = ""
    steps: list[ToolCall] = field(default_factory=list)
    checks: list[dict] = field(default_factory=list)
    blocked_by: str | None = None
    trace_id: str = ""
    latency_ms: float = 0.0
    cost: dict = field(default_factory=dict)