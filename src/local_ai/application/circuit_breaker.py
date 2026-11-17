import logging
import time
from dataclasses import dataclass
from enum import Enum

log = logging.getLogger(__name__)


class CBState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreaker:
    name: str
    failure_threshold: int = 5
    recovery_timeout_s: float = 30.0
    half_open_max_calls: int = 1

    _state: CBState = CBState.CLOSED
    _failures: int = 0
    _opened_at: float = 0.0
    _half_open_calls: int = 0

    def is_open(self) -> bool:
        if self._state == CBState.CLOSED:
            return False
        if self._state == CBState.OPEN:
            if time.time() - self._opened_at >= self.recovery_timeout_s:
                log.info("CB %s → HALF_OPEN", self.name)
                self._state = CBState.HALF_OPEN
                self._half_open_calls = 0
                return False
            return True
        if self._half_open_calls >= self.half_open_max_calls:
            return True
        self._half_open_calls += 1
        return False

    def on_success(self) -> None:
        if self._state != CBState.CLOSED:
            log.info("CB %s → CLOSED", self.name)
        self._state = CBState.CLOSED
        self._failures = 0
        self._half_open_calls = 0

    def on_failure(self) -> None:
        self._failures += 1
        if self._state == CBState.HALF_OPEN:
            log.warning("CB %s → OPEN (half-open failed)", self.name)
            self._state = CBState.OPEN
            self._opened_at = time.time()
        elif self._failures >= self.failure_threshold:
            log.warning("CB %s → OPEN (%d failures)", self.name, self._failures)
            self._state = CBState.OPEN
            self._opened_at = time.time()

    @property
    def state(self) -> str:
        return self._state.value


class CircuitBreakerRegistry:
    def __init__(self):
        self._breakers: dict[str, CircuitBreaker] = {}

    def get(self, name: str, **kwargs) -> CircuitBreaker:
        if name not in self._breakers:
            self._breakers[name] = CircuitBreaker(name=name, **kwargs)
        return self._breakers[name]


_registry: CircuitBreakerRegistry | None = None


def get_circuit_breakers() -> CircuitBreakerRegistry:
    global _registry
    if _registry is None:
        _registry = CircuitBreakerRegistry()
    return _registry