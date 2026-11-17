import logging
import re

log = logging.getLogger(__name__)


class InputGuard:
    SUSPICIOUS = [
        r"ignore (all )?(previous|above) instructions",
        r"you are now (DAN|developer mode|unrestricted)",
        r"<\|.*?\|>",
        r"system prompt (leak|reveal|print)",
    ]
    _compiled = [re.compile(p, re.I) for p in SUSPICIOUS]

    def check(self, text: str) -> tuple[bool, str]:
        for pattern in self._compiled:
            if pattern.search(text):
                log.warning("input guard: %s", pattern.pattern)
                return False, "input blocked (prompt injection suspected)"
        if len(text) > 20_000:
            return False, "input too long"
        return True, ""


class ToolGuard:
    def __init__(self, allowed_tools: set[str] | None = None, max_calls_per_turn: int = 5):
        self.allowed_tools = allowed_tools
        self.max_calls_per_turn = max_calls_per_turn
        self._calls = 0

    def reset_turn(self) -> None:
        self._calls = 0

    def check(self, tool_name: str, args: dict) -> tuple[bool, str]:
        if self.allowed_tools is not None and tool_name not in self.allowed_tools:
            return False, f"tool '{tool_name}' not in allowlist"
        if self._calls >= self.max_calls_per_turn:
            return False, "tool call budget exceeded"
        self._calls += 1
        return True, ""