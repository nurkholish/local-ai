from dataclasses import dataclass
from enum import Enum


class Severity(str, Enum):
    HARD = "hard"
    SOFT = "soft"


class Route(str, Enum):
    SIMPLE = "simple"
    RAG = "rag"
    EXTRACT = "extract"
    COMPLEX = "complex"


@dataclass(frozen=True)
class CheckResult:
    passed: bool
    name: str
    severity: Severity
    reason: str = ""