import json
from pathlib import Path
import cv2
from fastapi.testclient import TestClient
import numpy as np
import pytest
from sqlmodel import Session, select

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


def create_dummy_video(path: Path, duration_seconds: float = 4.0, fps: int = 10):
    """Generate a synthetic test video file using OpenCV."""
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    width, height = 320, 240
    writer = cv2.VideoWriter(str(path), fourcc, fps, (width, height))

    total_frames = int(duration_seconds * fps)
    for i in range(total_frames):
        # Create a frame with slightly varying intensity
        val = int((i / max(total_frames, 1)) * 255)
        frame = np.full((height, width, 3), val, dtype=np.uint8)
        cv2.putText(
            frame,
            f"Frame {i}",
            (20, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 255, 255),
            2,
        )
        writer.write(frame)

    writer.release()


def test_upload_valid_video(tmp_path):
    # 1. Create a worker and attempt in DB
    with Session(test_engine) as session:
        worker = Worker(
            name="Anil Kumar",
            language="English",
            area="Bangalore",
            consent=True,
            token="token-anil-123",
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

    # 2. Generate dummy video
    video_file = tmp_path / "valid_demo.mp4"
    create_dummy_video(video_file, duration_seconds=5.0, fps=10)

    # 3. Upload video
    with open(video_file, "rb") as f:
        res = client.post(
            f"/api/attempts/{attempt_id}/video?source=live",
            files={"file": ("valid_demo.mp4", f, "video/mp4")},
        )

    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["data"]["status"] == "analyzing"
    assert body["data"]["frames_count"] > 0

    # 4. Check DB row updated
    with Session(test_engine) as session:
        updated = session.exec(select(Attempt).where(Attempt.id == attempt_id)).first()
        assert updated is not None
        assert updated.status == "analyzing"
        assert updated.video_sha256 is not None
        assert updated.video_phash is not None
        assert updated.video_meta_json is not None

        meta = json.loads(updated.video_meta_json)
        assert meta["duration"] >= 4.5
        assert meta["frame_count"] == 50


def test_upload_empty_video():
    with Session(test_engine) as session:
        worker = session.exec(select(Worker)).first()
        attempt = create_attempt(worker_id=worker.id, skill_id="plumber_joint", db=session)
        attempt_id = attempt.id

    res = client.post(
        f"/api/attempts/{attempt_id}/video",
        files={"file": ("empty.mp4", b"", "video/mp4")},
    )
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "EMPTY_VIDEO"


def test_upload_corrupted_video():
    with Session(test_engine) as session:
        worker = session.exec(select(Worker)).first()
        attempt = create_attempt(worker_id=worker.id, skill_id="plumber_joint", db=session)
        attempt_id = attempt.id

    res = client.post(
        f"/api/attempts/{attempt_id}/video",
        files={"file": ("corrupt.mp4", b"this is not video data", "video/mp4")},
    )
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "INVALID_VIDEO"


def test_upload_video_too_short(tmp_path):
    with Session(test_engine) as session:
        worker = session.exec(select(Worker)).first()
        attempt = create_attempt(worker_id=worker.id, skill_id="plumber_joint", db=session)
        attempt_id = attempt.id

    # Create 1.5-second video (below 3.0s minimum)
    short_file = tmp_path / "short.mp4"
    create_dummy_video(short_file, duration_seconds=1.5, fps=10)

    with open(short_file, "rb") as f:
        res = client.post(
            f"/api/attempts/{attempt_id}/video",
            files={"file": ("short.mp4", f, "video/mp4")},
        )
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "VIDEO_TOO_SHORT"


def test_duplicate_video_fraud_detection(tmp_path):
    video_file = tmp_path / "shared_clip.mp4"
    create_dummy_video(video_file, duration_seconds=4.0, fps=10)

    with Session(test_engine) as session:
        worker = session.exec(select(Worker)).first()
        attempt1 = create_attempt(worker_id=worker.id, skill_id="mason_wall", db=session)
        attempt2 = create_attempt(worker_id=worker.id, skill_id="mason_wall", db=session)
        id1 = attempt1.id
        id2 = attempt2.id

    # First attempt uploads video
    with open(video_file, "rb") as f:
        res1 = client.post(
            f"/api/attempts/{id1}/video?source=live",
            files={"file": ("clip.mp4", f, "video/mp4")},
        )
    assert res1.status_code == 200

    # Second attempt uploads exact same video -> should flag duplicate
    with open(video_file, "rb") as f:
        res2 = client.post(
            f"/api/attempts/{id2}/video?source=upload",
            files={"file": ("clip.mp4", f, "video/mp4")},
        )
    assert res2.status_code == 200
    body2 = res2.json()
    assert body2["data"]["status"] == "analyzing"

    # Check fraud flags
    flags = [f["code"] for f in body2["data"]["fraud_flags"]]
    assert "DUPLICATE_VIDEO_SHA256" in flags
    assert "UPLOAD_SOURCE" in flags
