import time
from dataclasses import dataclass, field


@dataclass
class RetryBudget:
    total_budget_s: float = 120.0
    max_attempts: int = 3
    _started: float = field(default_factory=time.time)
    _attempts: int = 0

    def can_retry(self, min_needed_s: float = 1.0) -> bool:
        if self._attempts >= self.max_attempts:
            return False
        elapsed = time.time() - self._started
        return (self.total_budget_s - elapsed) > min_needed_s

    def consume(self) -> None:
        self._attempts += 1

    @property
    def remaining_s(self) -> float:
        return max(0, self.total_budget_s - (time.time() - self._started))

    @property
    def attempts(self) -> int:
        return self._attempts