import json
import logging
import re
from dataclasses import dataclass
from typing import Any

log = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    valid: bool
    data: Any = None
    reason: str = ""


def validate_json(text: str, required_fields: list[str] | None = None) -> ValidationResult:
    m = re.search(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", text, re.DOTALL)
    payload = m.group(1) if m else text
    try:
        data = json.loads(payload)
    except json.JSONDecodeError as e:
        return ValidationResult(False, None, f"invalid JSON: {e}")
    if required_fields:
        if not isinstance(data, dict):
            return ValidationResult(False, None, "expected object")
        missing = [f for f in required_fields if f not in data]
        if missing:
            return ValidationResult(False, None, f"missing fields: {missing}")
    return ValidationResult(True, data)