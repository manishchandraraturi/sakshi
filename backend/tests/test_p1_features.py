import json
from pathlib import Path
import cv2
from fastapi.testclient import TestClient
import numpy as np
import pytest
from sqlmodel import Session, select

from app.db import get_session
from app.main import app
from app.models import Attempt, AuditLog, Credential, Worker, utc_now
from app.services.attempt_service import create_attempt
from tests.test_routers import get_test_session, test_engine

client = TestClient(app)


@pytest.fixture(autouse=True)
def ensure_db_override():
    app.dependency_overrides[get_session] = get_test_session
    yield


def generate_test_video(path: Path, duration: float = 2.0, fps: int = 10) -> Path:
    """Generate a lightweight valid MP4 video for testing."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    width, height = 160, 120
    writer = cv2.VideoWriter(str(path), fourcc, fps, (width, height))
    total_frames = int(duration * fps)
    for i in range(total_frames):
        frame = np.full((height, width, 3), 128, dtype=np.uint8)
        cv2.putText(frame, f"F{i}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        writer.write(frame)
    writer.release()
    return path


# --- 1. Test DELETE /api/workers/{id}/data (T8.1) ---

def test_delete_worker_data_auth_checks():
    # 401 without auth header
    res = client.delete("/api/workers/non-existent/data")
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "UNAUTHORIZED"

    # 404 with invalid worker id
    res = client.delete(
        "/api/workers/non-existent/data",
        headers={"Authorization": "Bearer some-token"},
    )
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "WORKER_NOT_FOUND"


def test_delete_worker_data_token_mismatch():
    with Session(test_engine) as session:
        worker = Worker(
            name="Privacy Test Worker",
            language="English",
            area="South",
            consent=True,
            token="secret-token-worker-1",
        )
        session.add(worker)
        session.commit()
        session.refresh(worker)
        worker_id = worker.id

    # Wrong token -> 403
    res = client.delete(
        f"/api/workers/{worker_id}/data",
        headers={"Authorization": "Bearer wrong-token"},
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "FORBIDDEN"


def test_delete_worker_data_success(tmp_path):
    with Session(test_engine) as session:
        worker = Worker(
            name="Rahul Privacy",
            language="English",
            area="North",
            phone_optional="9876543210",
            consent=True,
            token="rahul-privacy-token",
        )
        session.add(worker)
        session.commit()
        session.refresh(worker)

        # Create attempt with video & frames
        attempt = create_attempt(worker_id=worker.id, skill_id="electrician_socket", db=session)
        
        # Create dummy video and frame on disk
        data_dir = Path(__file__).resolve().parent.parent / "data"
        videos_dir = data_dir / "videos"
        frames_dir = data_dir / "frames" / attempt.id
        videos_dir.mkdir(parents=True, exist_ok=True)
        frames_dir.mkdir(parents=True, exist_ok=True)

        test_video_path = videos_dir / f"{attempt.id}.mp4"
        test_video_path.write_bytes(b"dummy video data for deletion test")
        test_frame_path = frames_dir / "frame_000.jpg"
        test_frame_path.write_bytes(b"dummy frame")

        attempt.video_path = str(test_video_path).replace("\\", "/")
        session.add(attempt)

        # Create credential
        cred = Credential(
            attempt_id=attempt.id,
            worker_id=worker.id,
            skill_id="electrician_socket",
            tier=2,
            trust_score=80.0,
            payload_json=json.dumps({"worker": "Rahul Privacy"}),
            signature_b64="dummy-sig",
            evidence_sha256="dummy-hash",
            revoked=False,
        )
        session.add(cred)
        session.commit()
        session.refresh(worker)
        session.refresh(attempt)
        session.refresh(cred)

        worker_id = worker.id
        token = worker.token
        cred_id = cred.id

    # Verify file existed before
    assert test_video_path.exists()
    assert test_frame_path.exists()

    # Call DELETE /api/workers/{worker_id}/data
    res = client.delete(
        f"/api/workers/{worker_id}/data",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert "deleted successfully" in body["data"]["message"]

    # Verify files were erased from disk
    assert not test_video_path.exists()
    assert not frames_dir.exists()

    # Verify DB state
    with Session(test_engine) as session:
        updated_worker = session.exec(select(Worker).where(Worker.id == worker_id)).first()
        assert updated_worker.name == "Deleted Worker"
        assert updated_worker.phone_optional is None

        updated_cred = session.exec(select(Credential).where(Credential.id == cred_id)).first()
        assert updated_cred.revoked is True

        audit = session.exec(select(AuditLog).where(AuditLog.ref_id == worker_id)).first()
        assert audit is not None
        assert audit.action == "delete_my_data"


# --- 2. Test POST /api/attempts/{id}/rerecord (T8.4) ---

def test_rerecord_validation_errors(tmp_path):
    # Non-existent attempt
    dummy_video = generate_test_video(tmp_path / "rerecord_val.mp4")
    with open(dummy_video, "rb") as f:
        res = client.post(
            "/api/attempts/non-existent-attempt/rerecord",
            files={"file": ("rerecord.mp4", f, "video/mp4")},
            data={"step_ids": json.dumps(["step_1"])},
        )
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "ATTEMPT_NOT_FOUND"

    # Missing step_ids
    with Session(test_engine) as session:
        worker = session.exec(select(Worker)).first()
        attempt = create_attempt(worker_id=worker.id, skill_id="electrician_socket", db=session)
        attempt_id = attempt.id

    with open(dummy_video, "rb") as f:
        res = client.post(
            f"/api/attempts/{attempt_id}/rerecord",
            files={"file": ("rerecord.mp4", f, "video/mp4")},
            data={"step_ids": ""},
        )
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "STEP_IDS_REQUIRED"


def test_rerecord_step_merging_and_decision_update(tmp_path):
    # 1. Setup attempt with step_1 initially failed/unclear
    with Session(test_engine) as session:
        worker = session.exec(select(Worker)).first()
        attempt = create_attempt(worker_id=worker.id, skill_id="electrician_socket", db=session)
        attempt.status = "needs_rerecord"
        attempt.decision = "needs_rerecord"

        initial_ai_result = {
            "steps": [
                {"id": "step_1", "verdict": "unclear", "confidence": 0.4, "evidence_frames": [], "note": "Blurry"},
                {"id": "step_2", "verdict": "pass", "confidence": 0.9, "evidence_frames": [1], "note": "Clear"},
                {"id": "step_3", "verdict": "pass", "confidence": 0.9, "evidence_frames": [2], "note": "Clear"},
                {"id": "step_4", "verdict": "pass", "confidence": 0.9, "evidence_frames": [3], "note": "Clear"},
                {"id": "step_5", "verdict": "pass", "confidence": 0.9, "evidence_frames": [4], "note": "Clear"},
            ],
            "challenge_code_seen": True,
            "safety_items_seen": ["safety_gloves"],
        }
        attempt.ai_result_json = json.dumps(initial_ai_result)
        attempt.video_score = 60.0
        session.add(attempt)
        session.commit()
        session.refresh(attempt)
        attempt_id = attempt.id

    # 2. Re-record step_1
    rerecord_video = generate_test_video(tmp_path / "rerecord_sub.mp4", duration=2.0)
    with open(rerecord_video, "rb") as f:
        res = client.post(
            f"/api/attempts/{attempt_id}/rerecord",
            files={"file": ("rerecord.mp4", f, "video/mp4")},
            data={"step_ids": json.dumps(["step_1"])},
        )

    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    data = body["data"]

    # Verify step_1 was re-recorded and merged
    assert data["attempt_id"] == attempt_id
    assert "step_1" in data["rerecorded_steps"]
    
    # In MockAI / default mock provider, all evaluated steps return pass
    step_1_result = next((s for s in data["steps"] if s["id"] == "step_1"), None)
    assert step_1_result is not None
    assert step_1_result["verdict"] == "pass"

    # Decision should now update to accept and video_score should be passing
    assert data["decision"] == "accept"
    assert data["video_score"] >= 70.0
    assert data["status"] == "reviewed"

    # Verify DB update persisted
    with Session(test_engine) as session:
        updated_attempt = session.exec(select(Attempt).where(Attempt.id == attempt_id)).first()
        assert updated_attempt.decision == "accept"
        assert updated_attempt.status == "reviewed"
        persisted_ai = json.loads(updated_attempt.ai_result_json)
        persisted_s1 = next((s for s in persisted_ai["steps"] if s["id"] == "step_1"), None)
        assert persisted_s1["verdict"] == "pass"
