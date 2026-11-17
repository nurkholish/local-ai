from local_ai.application.circuit_breaker import CircuitBreaker


def test_cb_opens_after_threshold():
    cb = CircuitBreaker("test", failure_threshold=3, recovery_timeout_s=0.1)
    assert not cb.is_open()
    for _ in range(3):
        cb.on_failure()
    assert cb.is_open()


def test_cb_recovers_after_timeout():
    import time
    cb = CircuitBreaker("test", failure_threshold=2, recovery_timeout_s=0.05)
    cb.on_failure()
    cb.on_failure()
    assert cb.is_open()
    time.sleep(0.1)
    assert not cb.is_open()
    cb.on_success()
    assert cb.state == "closed"