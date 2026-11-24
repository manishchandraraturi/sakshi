import json
from fastapi.testclient import TestClient
import pytest
from sqlmodel import Session, select

from app.agent.review import run_review_decision
from app.ai.mock import MockAI
from app.db import get_session
from app.main import app
from app.models import Attempt, Worker
from app.services.attempt_service import create_attempt
from app.trust.score import check_safety_gate, video_score
from tests.test_routers import get_test_session, test_engine

client = TestClient(app)


@pytest.fixture(autouse=True)
def ensure_db_override():
    app.dependency_overrides[get_session] = get_test_session
    yield


# --- 1. Video Score & N1 Safety Gate Unit Tests ---
def test_video_score_all_pass():
    steps = [
        {"id": "s1", "verdict": "pass", "critical": True, "safety_critical": True},
        {"id": "s2", "verdict": "pass", "critical": False, "safety_critical": False},
        {"id": "s3", "verdict": "pass", "critical": True, "safety_critical": False},
    ]
    # Total weights: 2 + 1 + 2 = 5. All pass -> 5/5 = 100.0
    score = video_score(steps)
    assert score == 100.0


def test_video_score_critical_weighs_double():
    # Case A: Non-critical step fails (weight 1.0 lost out of 5.0)
    steps_non_crit_fail = [
        {"id": "s1", "verdict": "pass", "critical": True, "safety_critical": False},   # weight 2, earned 2
        {"id": "s2", "verdict": "fail", "critical": False, "safety_critical": False},   # weight 1, earned 0
        {"id": "s3", "verdict": "pass", "critical": True, "safety_critical": False},   # weight 2, earned 2
    ]
    score_a = video_score(steps_non_crit_fail)
    assert score_a == 80.0  # (4 / 5) * 100 = 80.0

    # Case B: Critical step fails (weight 2.0 lost out of 5.0)
    steps_crit_fail = [
        {"id": "s1", "verdict": "fail", "critical": True, "safety_critical": False},   # weight 2, earned 0
        {"id": "s2", "verdict": "pass", "critical": False, "safety_critical": False},   # weight 1, earned 1
        {"id": "s3", "verdict": "pass", "critical": True, "safety_critical": False},   # weight 2, earned 2
    ]
    score_b = video_score(steps_crit_fail)
    assert score_b == 60.0  # (3 / 5) * 100 = 60.0

    # Critical drop (40%) is exactly double non-critical drop (20%)
    assert (100.0 - score_b) == 2 * (100.0 - score_a)


def test_video_score_unclear_half_credit():
    steps = [
        {"id": "s1", "verdict": "pass", "critical": False, "safety_critical": False},     # weight 1, earned 1
        {"id": "s2", "verdict": "unclear", "critical": False, "safety_critical": False},  # weight 1, earned 0.5
    ]
    # Total possible 2, earned 1.5 -> (1.5 / 2) * 100 = 75.0
    score = video_score(steps)
    assert score == 75.0


def test_n1_safety_gate_triggers_zero_score():
    # Step 1 is safety_critical and fails
    steps_safety_fail = [
        {"id": "s1", "verdict": "fail", "critical": True, "safety_critical": True},
        {"id": "s2", "verdict": "pass", "critical": False, "safety_critical": False},
        {"id": "s3", "verdict": "pass", "critical": True, "safety_critical": False},
    ]
    score = video_score(steps_safety_fail)
    assert score == 0.0

    passed, failed_ids = check_safety_gate(steps_safety_fail)
    assert passed is False
    assert failed_ids == ["s1"]

    # Step 1 is safety_critical and unclear -> also capped at 0
    steps_safety_unclear = [
        {"id": "s1", "verdict": "unclear", "critical": True, "safety_critical": True},
        {"id": "s2", "verdict": "pass", "critical": False, "safety_critical": False},
        {"id": "s3", "verdict": "pass", "critical": True, "safety_critical": False},
    ]
    score_unclear = video_score(steps_safety_unclear)
    assert score_unclear == 0.0


# --- 2. Review Decision Logic Unit Tests ---
def test_review_decision_accept():
    with Session(test_engine) as session:
        worker = Worker(
            name="Raju",
            language="English",
            area="Bangalore",
            consent=True,
            token="token-raju",
        )
        session.add(worker)
        session.commit()
        session.refresh(worker)

        attempt = create_attempt(worker_id=worker.id, skill_id="electrician_socket", db=session)
        attempt.status = "analyzing"
        session.add(attempt)
        session.commit()
        session.refresh(attempt)

        # MockAI returns all passing
        result = run_review_decision(attempt=attempt, db=session)

        assert result["decision"] == "accept"
        assert result["video_score"] >= 70.0
        assert len(result["steps"]) > 0
        assert attempt.status == "reviewed"
        assert attempt.decision == "accept"


def test_review_decision_needs_rerecord_on_unclear_critical():
    with Session(test_engine) as session:
        worker = session.exec(select(Worker)).first()
        attempt = create_attempt(worker_id=worker.id, skill_id="electrician_socket", db=session)
        attempt.status = "analyzing"
        session.add(attempt)
        session.commit()
        session.refresh(attempt)

        # Mock AI returns step_1 (which is critical and safety_critical) as unclear
        mock_unclear_ai = MockAI(
            custom_response=json.dumps(
                {
                    "steps": [
                        {"id": "step_1", "verdict": "unclear", "confidence": 0.5, "evidence_frames": [], "note": "Blurry"},
                        {"id": "step_2", "verdict": "pass", "confidence": 0.9, "evidence_frames": [1], "note": "Ok"},
                        {"id": "step_3", "verdict": "pass", "confidence": 0.9, "evidence_frames": [2], "note": "Ok"},
                        {"id": "step_4", "verdict": "pass", "confidence": 0.9, "evidence_frames": [3], "note": "Ok"},
                        {"id": "step_5", "verdict": "pass", "confidence": 0.9, "evidence_frames": [4], "note": "Ok"},
                    ],
                    "challenge_code_seen": True,
                    "safety_items_seen": ["safety_gloves"],
                    "video_quality": {"rating": "poor", "reason": "Blurry frame"},
                }
            )
        )

        result = run_review_decision(attempt=attempt, db=session, ai_provider=mock_unclear_ai)

        assert result["decision"] == "needs_rerecord"
        assert "step_1" in result["rerecord_step_ids"]
        assert attempt.status == "reviewed"
        assert attempt.decision == "needs_rerecord"


def test_review_decision_reject_on_fraud_flags():
    with Session(test_engine) as session:
        worker = session.exec(select(Worker)).first()
        attempt = create_attempt(worker_id=worker.id, skill_id="electrician_socket", db=session)
        attempt.status = "analyzing"
        attempt.fraud_flags_json = json.dumps([{"code": "DUPLICATE_VIDEO_SHA256", "detail": "Reused video"}])
        session.add(attempt)
        session.commit()
        session.refresh(attempt)

        result = run_review_decision(attempt=attempt, db=session)

        assert result["decision"] == "reject"
        assert len(result["fraud_flags"]) > 0
        assert attempt.decision == "reject"


# --- 3. GET /api/attempts/{id} Non-Blocking Integration Test ---
def test_get_attempt_does_not_block_synchronously():
    with Session(test_engine) as session:
        worker = session.exec(select(Worker)).first()
        attempt = create_attempt(worker_id=worker.id, skill_id="electrician_socket", db=session)
        attempt.status = "analyzing"
        session.add(attempt)
        session.commit()
        session.refresh(attempt)
        attempt_id = attempt.id

    res = client.get(f"/api/attempts/{attempt_id}")
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    data = body["data"]

    # Status remains analyzing without blocking
    assert data["status"] == "analyzing"
    assert data["decision"] is None
    assert "agent_log" in data
