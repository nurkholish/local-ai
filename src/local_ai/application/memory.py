import logging
from dataclasses import dataclass, field

log = logging.getLogger(__name__)


@dataclass
class MemoryWindow:
    max_turns: int = 12
    history: list[dict] = field(default_factory=list)

    def add(self, role: str, content: str) -> None:
        self.history.append({"role": role, "content": content})
        if len(self.history) > self.max_turns * 2:
            self.history = self.history[-self.max_turns * 2:]

    def get_messages(self) -> list[dict]:
        return list(self.history)

    def clear(self) -> None:
        self.history.clear()