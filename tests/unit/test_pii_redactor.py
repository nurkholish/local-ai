from local_ai.application.pii_redactor import PIIRedactor


def test_redact_email():
    r = PIIRedactor()
    out = r.redact("contact john@example.com")
    assert "john@example.com" not in out
    assert "[REDACTED_EMAIL]" in out


def test_redact_api_key():
    r = PIIRedactor()
    out = r.redact("key: sk-abcdefghijklmnopqrstuvwxyz")
    assert "sk-" not in out


def test_disabled():
    r = PIIRedactor(enabled=False)
    text = "a@b.com"
    assert r.redact(text) == text