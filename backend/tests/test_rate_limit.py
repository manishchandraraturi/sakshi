from fastapi.testclient import TestClient
import pytest
from sqlmodel import Session

from app.db import get_session
from app.main import app
from app.utils.rate_limiter import (
    InMemoryRateLimiter,
    RateLimitExceeded,
    witness_vouch_limiter,
    worker_signup_limiter,
)
from tests.test_routers import get_test_session, test_engine

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_rate_limiters():
    app.dependency_overrides[get_session] = get_test_session
    worker_signup_limiter.reset()
    witness_vouch_limiter.reset()
    yield
    worker_signup_limiter.reset()
    witness_vouch_limiter.reset()


def test_worker_signup_rate_limit_exceeded():
    """
    POST /api/workers has a max limit of 5 requests per 60 seconds.
    Verify that the 6th request returns HTTP 429 Too Many Requests.
    """
    worker_signup_limiter.reset()

    payload = {
        "name": "Rate Limit Test Worker",
        "language": "English",
        "area": "Bengaluru",
        "consent": True,
        "device_fp": "fp_rate_test",
    }

    # Requests 1 to 5 should succeed
    for i in range(5):
        res = client.post("/api/workers", json={**payload, "name": f"Worker {i}"})
        assert res.status_code == 200, f"Request {i+1} failed with status {res.status_code}"
        assert res.json()["ok"] is True

    # 6th request must exceed the rate limit
    res_6 = client.post("/api/workers", json={**payload, "name": "Worker 6"})
    assert res_6.status_code == 429
    body = res_6.json()
    assert body["ok"] is False
    assert body["error"] is not None
    assert body["error"]["code"] == "RATE_LIMIT"
    assert "Too many requests" in body["error"]["message"]
    assert "Retry-After" in res_6.headers


def test_witness_vouch_rate_limit_exceeded():
    """
    POST /api/w/{token}/vouch rate limit test.
    Verify that exceeding the max limit returns HTTP 429 Too Many Requests.
    """
    witness_vouch_limiter.reset()

    vouch_payload = {
        "witness_name": "Test Witness",
        "role": "peer",
        "seen_in_person": True,
        "known_years_bucket": "1_3",
        "would_hire": True,
        "verdict": "yes",
        "device_fp": "fp_witness_limiter",
    }

    limit = witness_vouch_limiter.max_requests
    for i in range(limit):
        res = client.post("/api/w/dummy_token/vouch", json=vouch_payload)
        assert res.status_code != 429

    # Next request must be intercepted by rate limiter
    res_exceeded = client.post("/api/w/dummy_token/vouch", json=vouch_payload)
    assert res_exceeded.status_code == 429
    body = res_exceeded.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "RATE_LIMIT"
    assert "Too many requests" in body["error"]["message"]


def test_in_memory_rate_limiter_unit():
    """Unit test the InMemoryRateLimiter sliding window tracking and reset."""
    limiter = InMemoryRateLimiter(max_requests=2, window_seconds=10)

    class DummyRequest:
        def __init__(self, ip: str):
            self.headers = {}
            self.client = type("Client", (), {"host": ip})()

    req = DummyRequest("192.168.1.100")

    # 2 requests pass
    limiter.check(req)
    limiter.check(req)

    # 3rd request raises
    with pytest.raises(RateLimitExceeded) as exc:
        limiter.check(req)
    assert exc.value.retry_after > 0

    # Reset clears tracking
    limiter.reset()
    limiter.check(req)  # Should pass now
