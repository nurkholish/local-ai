import logging
from dataclasses import dataclass

log = logging.getLogger(__name__)

PRICING = {
    "gpt-4o-mini": {"in": 0.15, "out": 0.60},
    "gpt-4o": {"in": 2.50, "out": 10.00},
    "gpt-4.1": {"in": 2.00, "out": 8.00},
    "claude-3-5-sonnet": {"in": 3.00, "out": 15.00},
    "claude-3-5-haiku": {"in": 0.80, "out": 4.00},
    "local": {"in": 0.0, "out": 0.0},
}


@dataclass
class CostAccumulator:
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def cost_usd(self) -> float:
        price = PRICING.get(self.model, PRICING["local"])
        return (
            (self.input_tokens / 1_000_000) * price["in"]
            + (self.output_tokens / 1_000_000) * price["out"]
        )

    def record(self, usage: dict | None, model: str) -> None:
        if not usage:
            return
        self.model = model
        self.input_tokens += usage.get("prompt_tokens", 0)
        self.output_tokens += usage.get("completion_tokens", 0)

    def to_dict(self) -> dict:
        return {
            "model": self.model,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "cost_usd": round(self.cost_usd, 6),
        }