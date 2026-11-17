from local_ai.application.checks import OutputChecks


def test_empty_fails():
    c = OutputChecks()
    results = c.run("", {})
    passed, _ = c.aggregate(results)
    assert not passed


def test_grounded_calc():
    c = OutputChecks()
    ctx = {"tool_results": [{"tool": "calculator", "result": "391"}]}
    results = c.run("The answer is 391", ctx)
    grounded = next(r for r in results if r.name == "grounded")
    assert grounded.passed