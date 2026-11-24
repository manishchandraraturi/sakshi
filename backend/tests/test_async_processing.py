"""
backend/tests/test_async_processing.py

Tests for Phase 11 asynchronous video processing:
1. Video upload returns status 'analyzing' immediately and schedules background analysis.
2. Background task executes analysis in an isolated DB session and transitions status to 'reviewed'.
3. GET /api/attempts/{id} is purely non-blocking and reads database status directly.
"""
from pathlib import Path
import cv2
from fastapi.testclient import TestClient
import numpy as np
import pytest
from sqlmodel import Session, select

from app.db import get_session
from app.main import app
from app.models import Attempt, Worker
from app.routers.video import process_video_analysis_task
from app.services.attempt_service import create_attempt
from tests.test_routers import get_test_session, test_engine

client = TestClient(app)


@pytest.fixture(autouse=True)
def ensure_db_override():
    app.dependency_overrides[get_session] = get_test_session
    yield


def create_dummy_video(path: Path, duration_seconds: float = 4.0, fps: int = 10):
    """Generate a synthetic test video file."""
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    width, height = 320, 240
    writer = cv2.VideoWriter(str(path), fourcc, fps, (width, height))

    total_frames = int(duration_seconds * fps)
    for i in range(total_frames):
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


def test_get_attempt_non_blocking_read():
    """Verify GET /api/attempts/{id} returns database status directly without blocking."""
    with Session(test_engine) as session:
        worker = Worker(name="Async Candidate", area="Bangalore", language="en", consent=True, token="tok-async-1")
        session.add(worker)
        session.commit()
        session.refresh(worker)

        attempt = create_attempt(worker.id, "electrician_socket", session)
        attempt.status = "analyzing"
        session.add(attempt)
        session.commit()
        session.refresh(attempt)
        attempt_id = attempt.id

    res = client.get(f"/api/attempts/{attempt_id}")
    assert res.status_code == 200
    data = res.json()["data"]

    # Returns analyzing without synchronously triggering review
    assert data["status"] == "analyzing"
    assert data["decision"] is None
    assert data["video_score"] is None


def test_video_upload_triggers_background_processing(tmp_path):
    """
    Verify video upload schedules background processing which updates the attempt to reviewed.
    """
    with Session(test_engine) as session:
        worker = Worker(name="Async Uploader", area="Bangalore", language="en", consent=True, token="tok-async-2")
        session.add(worker)
        session.commit()
        session.refresh(worker)

        attempt = create_attempt(worker.id, "electrician_socket", session)
        attempt.status = "awaiting_video"
        session.add(attempt)
        session.commit()
        session.refresh(attempt)
        attempt_id = attempt.id

    video_file = tmp_path / "test_async_demo.mp4"
    create_dummy_video(video_file, duration_seconds=5.0)

    with open(video_file, "rb") as f:
        res = client.post(
            f"/api/attempts/{attempt_id}/video?source=live",
            files={"file": ("test_async_demo.mp4", f, "video/mp4")},
        )

    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["data"]["status"] == "analyzing"

    # Because TestClient processes background tasks before response returns,
    # the background task executed and updated status in DB
    with Session(test_engine) as session:
        updated = session.exec(select(Attempt).where(Attempt.id == attempt_id)).first()
        assert updated is not None
        assert updated.status == "reviewed"
        assert updated.video_score is not None
        assert updated.decision in ("accept", "needs_rerecord", "reject")


def test_process_video_analysis_task_isolated():
    """Verify background task runs cleanly with its own database session."""
    with Session(test_engine) as session:
        worker = Worker(name="Isolated Worker", area="Bangalore", language="en", consent=True, token="tok-async-3")
        session.add(worker)
        session.commit()
        session.refresh(worker)

        attempt = create_attempt(worker.id, "plumber_joint", session)
        attempt.status = "analyzing"
        session.add(attempt)
        session.commit()
        session.refresh(attempt)
        attempt_id = attempt.id

    # Run the background worker task directly
    process_video_analysis_task(attempt_id)

    with Session(test_engine) as session:
        finished = session.exec(select(Attempt).where(Attempt.id == attempt_id)).first()
        assert finished.status == "reviewed"
        assert finished.video_score is not None
