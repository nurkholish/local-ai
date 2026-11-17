from local_ai.application.validators import validate_json


def test_valid_json_plain():
    r = validate_json('{"name": "alice"}')
    assert r.valid
    assert r.data["name"] == "alice"


def test_valid_json_in_codeblock():
    r = validate_json('```json\n{"x": 1}\n```')
    assert r.valid


def test_invalid_json():
    r = validate_json("not json")
    assert not r.valid
    assert "invalid JSON" in r.reason


def test_required_fields():
    r = validate_json('{"a": 1}', required_fields=["a", "b"])
    assert not r.valid
    assert "missing fields" in r.reason