import logging
import re

log = logging.getLogger(__name__)

PATTERNS = {
    "email": re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"),
    "phone_id": re.compile(r"\b(?:\+62|62|0)[\s-]?8\d{1,3}[\s-]?\d{3,4}[\s-]?\d{3,4}\b"),
    "nik": re.compile(r"\b\d{16}\b"),
    "credit_card": re.compile(r"\b(?:\d[ -]?){13,19}\b"),
    "ipv4": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    "api_key_sk": re.compile(r"\bsk-[a-zA-Z0-9]{20,}\b"),
    "api_key_ghp": re.compile(r"\bghp_[a-zA-Z0-9]{20,}\b"),
}


class PIIRedactor:
    def __init__(self, enabled: bool = True, redact_on_output: bool = True):
        self.enabled = enabled
        self.redact_on_output = redact_on_output
        self._hits = 0

    def redact(self, text: str) -> str:
        if not self.enabled or not text:
            return text

        redacted = text
        for label, pattern in PATTERNS.items():
            def _replace(m: re.Match) -> str:
                self._hits += 1
                log.info("PII redacted: %s", label)
                return f"[REDACTED_{label.upper()}]"
            redacted = pattern.sub(_replace, redacted)

        return redacted

    @property
    def total_hits(self) -> int:
        return self._hits