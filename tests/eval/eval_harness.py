import asyncio
import json
import random
import sys
from dataclasses import dataclass
from pathlib import Path

from local_ai.application.use_cases.run_agent import RunAgentUseCase
from local_ai.config import get_settings
from local_ai.domain.entities import AgentRequest
from local_ai.infrastructure.llm.router import LLMRouter


@dataclass
class Case:
    input: str
    expected_tools: list[str]
    must_contain: list[str] | None = None


def load_cases(path: str) -> list[Case]:
    cases = []
    for line in Path(path).read_text().splitlines():
        if not line.strip():
            continue
        d = json.loads(line)
        cases.append(Case(d["input"], d.get("expected_tools", []), d.get("must_contain")))
    return cases


def bootstrap_ci(scores: list[int], n_boot: int = 1000, alpha: float = 0.05):
    if not scores:
        return (0.0, 0.0, 0.0)
    n = len(scores)
    means = sorted(sum(random.choice(scores) for _ in range(n)) / n for _ in range(n_boot))
    return (sum(scores) / n, means[int(n_boot * alpha / 2)], means[int(n_boot * (1 - alpha / 2))])


async def evaluate():
    s = get_settings()
    llm = LLMRouter(s)
    uc = RunAgentUseCase(llm=llm, settings=s)
    cases = load_cases("tests/eval/eval_set.jsonl")
    per_case: list[int] = []
    for c in cases:
        try:
            r = await uc.execute(AgentRequest(message=c.input))
        except Exception as e:
            print(f"  [ERR] {c.input[:50]} -> {e}")
            per_case.append(0)
            continue
        tools = [step.name for step in r.steps]
        ok = all(t in tools for t in c.expected_tools)
        if c.must_contain:
            ok = ok and all(m in r.answer for m in c.must_contain)
        per_case.append(1 if ok else 0)
        print(f"  [{'PASS' if ok else 'FAIL'}] {c.input[:60]}")

    mean, lo, hi = bootstrap_ci(per_case)
    print(f"\nAccuracy: {mean:.3f}  95% CI: [{lo:.3f}, {hi:.3f}]  n={len(per_case)}")
    if lo < 0.5:
        print("WARNING: regression likely")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(evaluate())