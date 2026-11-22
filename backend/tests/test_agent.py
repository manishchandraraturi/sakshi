import json
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.agent.loop import run_interview_step
from app.agent.state import InterviewState
from app.ai.mock import MockAI
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


def test_full_interview_flow_api():
    with Session(test_engine) as session:
        worker = Worker(
            name="Ramesh Kumar",
            language="Hindi",
            area="Bangalore",
            consent=True,
            device_fp="fp-test-123",
            token="test-token-456",
        )
        session.add(worker)
        session.commit()
        session.refresh(worker)

        attempt = create_attempt(
            worker_id=worker.id,
            skill_id="electrician_socket",
            db=session,
        )
        attempt_id = attempt.id

    # 1. First call with no answer (Q1)
    res1 = client.post(
        f"/api/attempts/{attempt_id}/interview/next",
        json={"answer": None},
    )
    assert res1.status_code == 200
    body1 = res1.json()
    assert body1["ok"] is True
    assert body1["data"]["done"] is False
    assert "What do you check" in body1["data"]["question"]
    assert body1["data"]["progress"] == {"current": 1, "total": 3}

    # 2. Answer Q1 -> should return Q2
    res2 = client.post(
        f"/api/attempts/{attempt_id}/interview/next",
        json={"answer": "Turn off main MCB and verify no voltage with a tester."},
    )
    assert res2.status_code == 200
    body2 = res2.json()
    assert body2["ok"] is True
    assert body2["data"]["done"] is False
    assert "phase wire" in body2["data"]["question"]
    assert body2["data"]["progress"] == {"current": 2, "total": 3}

    # 3. Answer Q2 -> should return Q3
    res3 = client.post(
        f"/api/attempts/{attempt_id}/interview/next",
        json={"answer": "Cutting phase ensures appliance has no live power when switch is OFF."},
    )
    assert res3.status_code == 200
    body3 = res3.json()
    assert body3["ok"] is True
    assert body3["data"]["done"] is False
    assert "earth wire" in body3["data"]["question"]
    assert body3["data"]["progress"] == {"current": 3, "total": 3}

    # 4. Answer Q3 -> interview completed
    res4 = client.post(
        f"/api/attempts/{attempt_id}/interview/next",
        json={"answer": "Never leave it ungrounded, inform contractor and run a new earth wire."},
    )
    assert res4.status_code == 200
    body4 = res4.json()
    assert body4["ok"] is True
    assert body4["data"]["done"] is True
    assert body4["data"]["question"] is None
    assert body4["data"]["progress"] == {"current": 3, "total": 3}

    # 5. Verify DB state
    with Session(test_engine) as session:
        updated_attempt = session.exec(select(Attempt).where(Attempt.id == attempt_id)).first()
        assert updated_attempt is not None
        assert updated_attempt.status == "awaiting_video"
        assert updated_attempt.interview_score == 85.0
        assert updated_attempt.interview_json is not None

        state = InterviewState.model_validate_json(updated_attempt.interview_json)
        assert state.is_done is True
        assert len(state.answers) == 3
        assert len(state.scores) == 3

    # 6. Subsequent call when already done returns 400
    res5 = client.post(
        f"/api/attempts/{attempt_id}/interview/next",
        json={"answer": "Extra answer"},
    )
    assert res5.status_code == 400
    assert res5.json()["error"]["code"] == "INVALID_ATTEMPT_STATUS"

    # 7. Non-existent attempt returns 404
    res_404 = client.post(
        "/api/attempts/non-existent-id/interview/next",
        json={"answer": "Test"},
    )
    assert res_404.status_code == 404
    assert res_404.json()["error"]["code"] == "ATTEMPT_NOT_FOUND"


def test_interview_step_with_followup():
    with Session(test_engine) as session:
        worker = Worker(
            name="Suresh",
            language="English",
            area="Mysore",
            consent=True,
            token="token-suresh",
        )
        session.add(worker)
        session.commit()
        session.refresh(worker)

        attempt = create_attempt(
            worker_id=worker.id,
            skill_id="electrician_socket",
            db=session,
        )

        # 1. Ask initial question
        res_initial = run_interview_step(attempt=attempt, answer=None, db=session)
        assert res_initial.done is False
        assert "What do you check" in res_initial.question

        # 2. Candidate gives vague answer -> MockAI returns followup
        mock_ai_followup = MockAI(
            custom_response=json.dumps(
                {
                    "score": 50,
                    "missing_points": ["testing for voltage"],
                    "next": {
                        "type": "followup",
                        "text": "How do you test if voltage is present?",
                    },
                }
            )
        )
        res_followup = run_interview_step(
            attempt=attempt,
            answer="I just turn off the switch",
            db=session,
            ai=mock_ai_followup,
        )
        assert res_followup.done is False
        assert res_followup.question == "How do you test if voltage is present?"
        assert res_followup.progress["current"] == 1

        state = InterviewState.model_validate_json(attempt.interview_json)
        assert state.follow_up_count == 1
        assert state.current_question_index == 0

        # 3. Candidate answers followup -> MockAI accepts and advances to question 2
        mock_ai_q2 = MockAI(
            custom_response=json.dumps(
                {
                    "score": 90,
                    "missing_points": [],
                    "next": {
                        "type": "question",
                        "text": "Next question",
                    },
                }
            )
        )
        res_q2 = run_interview_step(
            attempt=attempt,
            answer="I test it with a neon tester on both terminals",
            db=session,
            ai=mock_ai_q2,
        )
        assert res_q2.done is False
        assert "phase wire" in res_q2.question
        assert res_q2.progress["current"] == 2

        state2 = InterviewState.model_validate_json(attempt.interview_json)
        assert state2.current_question_index == 1
        assert state2.follow_up_count == 1
