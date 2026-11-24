from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine, select
from app.db import get_session
from app.main import app
from app.models import Attempt, Worker
from app.services.attempt_service import generate_challenge_code

# Setup an isolated in-memory test database with StaticPool so all connections share the DB
test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
SQLModel.metadata.create_all(test_engine)


def get_test_session():
    with Session(test_engine) as session:
        yield session


app.dependency_overrides[get_session] = get_test_session
client = TestClient(app)


def test_challenge_code_generator():
    code = generate_challenge_code()
    assert len(code) == 4
    assert code.isalnum()
    assert code == code.upper()


def test_get_skills():
    res = client.get("/api/skills")
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["error"] is None
    data = body["data"]
    assert len(data) == 5
    trades = {item["trade"] for item in data}
    assert trades == {"Electrician", "Plumber", "Mason", "Welder", "Carpenter"}

    # Verify first skill has steps
    first_skill = data[0]["skills"][0]
    assert "id" in first_skill
    assert "name" in first_skill
    assert len(first_skill["steps"]) >= 4
    assert "critical" in first_skill["steps"][0]


def test_create_worker_and_attempt_flow():
    # 1. Test worker creation without consent (should fail)
    res_no_consent = client.post(
        "/api/workers",
        json={
            "name": "Ravi Kumar",
            "language": "kn",
            "area": "Bangalore North",
            "consent": False,
            "device_fp": "fp_test_123",
        },
    )
    assert res_no_consent.status_code == 400
    assert res_no_consent.json()["ok"] is False
    assert res_no_consent.json()["error"]["code"] == "CONSENT_REQUIRED"

    # 2. Test valid worker creation
    res_worker = client.post(
        "/api/workers",
        json={
            "name": "Ravi Kumar",
            "language": "kn",
            "area": "Bangalore North",
            "consent": True,
            "device_fp": "fp_test_123",
        },
    )
    assert res_worker.status_code == 200
    worker_body = res_worker.json()
    assert worker_body["ok"] is True
    worker_data = worker_body["data"]
    worker_id = worker_data["worker_id"]
    token = worker_data["token"]
    assert len(worker_id) > 0
    assert len(token) > 0

    # 3. Test attempt creation with invalid skill
    res_invalid_skill = client.post(
        "/api/attempts",
        headers={"Authorization": f"Bearer {token}"},
        json={"skill_id": "nonexistent_skill"},
    )
    assert res_invalid_skill.status_code == 400
    assert res_invalid_skill.json()["ok"] is False

    # 4. Test attempt creation with valid skill and bearer token
    res_attempt = client.post(
        "/api/attempts",
        headers={"Authorization": f"Bearer {token}"},
        json={"skill_id": "electrician_socket"},
    )
    assert res_attempt.status_code == 200
    attempt_body = res_attempt.json()
    assert attempt_body["ok"] is True
    attempt_data = attempt_body["data"]
    attempt_id = attempt_data["attempt_id"]
    challenge_code = attempt_data["challenge_code"]
    checklist = attempt_data["checklist"]

    assert len(attempt_id) > 0
    assert len(challenge_code) == 4
    assert len(checklist) >= 5

    # 5. Verify DB persistence in test_engine
    with Session(test_engine) as session:
        db_worker = session.exec(select(Worker).where(Worker.id == worker_id)).first()
        assert db_worker is not None
        assert db_worker.name == "Ravi Kumar"
        assert db_worker.token == token

        db_attempt = session.exec(select(Attempt).where(Attempt.id == attempt_id)).first()
        assert db_attempt is not None
        assert db_attempt.worker_id == worker_id
        assert db_attempt.skill_id == "electrician_socket"
        assert db_attempt.status == "interviewing"
        assert db_attempt.challenge_code == challenge_code
