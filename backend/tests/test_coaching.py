import json
from fastapi.testclient import TestClient
import pytest
from sqlmodel import Session, select

from app.agent.coach import generate_coaching
from app.agent.prompts import build_coach_system_prompt, build_coach_user_prompt
from app.ai.mock import MockAI
from app.blueprints.loader import load_blueprint
from app.db import get_session
from app.main import app
from app.models import Attempt, Worker
from app.services.attempt_service import create_attempt
from tests.test_routers import get_test_session, test_engine

client = TestClient(app)


@pytest.fixture(autouse=True)
def ensure_db_override():
    app.dependency_overrides[get_session] = get_test_session
    yield


def test_coach_prompts():
    sys_prompt = build_coach_system_prompt("Hindi")
    assert "Hindi" in sys_prompt
    assert "unclear_steps_tips" in sys_prompt

    user_prompt = build_coach_user_prompt(
        trade="Electrician",
        skill_name="Socket Board",
        decision="needs_rerecord",
        score=50.0,
        failed_steps=[{"id": "strip_wire", "title": "Strip Wire", "verdict": "fail", "note": "Bare wire not shown"}],
        witness_status="None",
        tier=0,
    )
    assert "strip_wire" in user_prompt
    assert "Electrician" in user_prompt


def test_generate_coaching_mock_ai():
    with Session(test_engine) as session:
        worker = Worker(name="Test Worker", language="English", area="Delhi", consent=True, device_fp="fp1", token="tok1")
        session.add(worker)
        session.commit()
        session.refresh(worker)

        blueprint = load_blueprint("electrician_socket")
        attempt = create_attempt(worker_id=worker.id, skill_id="electrician_socket", db=session)
        attempt.ai_result_json = json.dumps({
            "steps": [
                {"id": "strip_wire", "verdict": "fail", "confidence": 0.3, "note": "Wire cut too short"},
                {"id": "secure_terminal", "verdict": "pass", "confidence": 0.9, "note": "Secure"},
            ],
            "challenge_code_seen": True,
            "safety_items_seen": ["safety_gloves"],
            "video_quality": {"rating": "good", "reason": "Clear"},
        })
        attempt.decision = "needs_rerecord"
        attempt.video_score = 50.0
        session.add(attempt)
        session.commit()
        session.refresh(attempt)

        coaching = generate_coaching(attempt, blueprint, ai_provider=MockAI(), db=session)
        assert "summary" in coaching
        assert "next_actions" in coaching
        assert len(coaching["next_actions"]) <= 3
        assert "unclear_steps_tips" in coaching
        assert len(coaching["unclear_steps_tips"]) > 0
        assert coaching["unclear_steps_tips"][0]["step_id"] == "strip_wire"


def test_attempt_get_includes_coaching():
    with Session(test_engine) as session:
        worker = Worker(name="Test Worker 2", language="English", area="Delhi", consent=True, device_fp="fp2", token="tok2")
        session.add(worker)
        session.commit()
        session.refresh(worker)

        attempt = create_attempt(worker_id=worker.id, skill_id="electrician_socket", db=session)
        coaching_dict = {
            "summary": "Demonstrated good technique.",
            "next_actions": ["Invite witnesses"],
            "unclear_steps_tips": [],
        }
        attempt.coaching_json = json.dumps(coaching_dict)
        session.add(attempt)
        session.commit()
        session.refresh(attempt)
        attempt_id = attempt.id

    res = client.get(f"/api/attempts/{attempt_id}")
    assert res.status_code == 200
    data = res.json()["data"]
    assert "coaching" in data
    assert data["coaching"]["summary"] == "Demonstrated good technique."
    assert data["coaching"]["next_actions"] == ["Invite witnesses"]
