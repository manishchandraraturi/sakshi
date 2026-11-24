import os
import sys
import pytest
from app.ai.mock import MockAI
from app.config import settings


@pytest.fixture(autouse=True)
def force_test_mode(monkeypatch):
    """
    Ensure the test suite never makes external network calls to Gemini and runs in <30s.
    Forces settings.DEMO_MODE = True and monkeypatches get_default_ai to return MockAI.
    """
    monkeypatch.setattr(settings, "DEMO_MODE", True)

    mock_instance = MockAI()

    import app.agent.loop
    import app.agent.review
    import app.agent.coach

    monkeypatch.setattr(app.agent.loop, "get_default_ai", lambda: mock_instance)
    monkeypatch.setattr(app.agent.review, "get_default_ai", lambda: mock_instance)
    monkeypatch.setattr(app.agent.coach, "get_default_ai", lambda: mock_instance)

    from app.utils.rate_limiter import witness_vouch_limiter, worker_signup_limiter
    worker_signup_limiter.reset()
    witness_vouch_limiter.reset()
