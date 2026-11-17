import logging
import re

from local_ai.domain.value_objects import CheckResult, Severity

log = logging.getLogger(__name__)


class OutputChecks:
    def _check_not_empty(self, output: str, ctx: dict) -> CheckResult:
        ok = bool(output and output.strip())
        return CheckResult(ok, "not_empty", Severity.HARD, "" if ok else "empty output")

    def _check_no_system_leak(self, output: str, ctx: dict) -> CheckResult:
        sp = ctx.get("system_prompt", "")
        ok = sp not in output if sp else True
        return CheckResult(ok, "no_system_leak", Severity.HARD, "" if ok else "system leak")

    def _check_no_pii(self, output: str, ctx: dict) -> CheckResult:
        pii = re.search(r"[\w.-]+@[\w.-]+\.\w+|\b\+?\d{10,15}\b", output)
        return CheckResult(pii is None, "no_pii", Severity.SOFT, "" if pii is None else "PII?")

    def _check_length(self, output: str, ctx: dict) -> CheckResult:
        ok = len(output) <= 8000
        return CheckResult(ok, "length", Severity.SOFT, "" if ok else "too long")

    def _check_grounded(self, output: str, ctx: dict) -> CheckResult:
        results = ctx.get("tool_results", [])
        calcs = [r for r in results if r.get("tool") == "calculator"]
        if not calcs:
            return CheckResult(True, "grounded", Severity.SOFT)
        expected = calcs[-1].get("result", "")
        ok = expected in output
        return CheckResult(ok, "grounded", Severity.SOFT, "" if ok else "not grounded")

    def run(self, output: str, ctx: dict) -> list[CheckResult]:
        checks = [
            self._check_not_empty,
            self._check_no_system_leak,
            self._check_no_pii,
            self._check_length,
            self._check_grounded,
        ]
        results = []
        for c in checks:
            try:
                results.append(c(output, ctx))
            except Exception:
                log.exception("check %s crashed", c.__name__)
                results.append(CheckResult(False, c.__name__, Severity.SOFT, "crashed"))
        return results

    @staticmethod
    def aggregate(results: list[CheckResult]) -> tuple[bool, list[CheckResult]]:
        hard = [r for r in results if not r.passed and r.severity == Severity.HARD]
        for r in results:
            if not r.passed:
                log.warning("check failed: %s (%s) %s", r.name, r.severity, r.reason)
        return (len(hard) == 0, hard)