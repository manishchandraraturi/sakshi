"""
backend/tests/test_audit_regressions.py

Regression test suite for audit issues:
1. Video metadata extraction for .webm files via FFmpeg / OpenCV fallback.
2. MockAI rejection of adversarial triggers ('my pant is wet') and unrecognized inputs.
3. Deterministic Tier Engine rules (Tier 1 threshold, Tier 3 trainer/employer requirement).
4. N1 Safety Gate: 'fail' or 'unclear' on safety_critical step caps video score and Tier at 0.
5. Duplicate device fingerprint among witnesses returns 0.0 weight.
6. Witness role downgrade to 'peer' when trainer/employer lacks institute code or credential.
7. Canonical Ed25519 payload contains 'valid_until' 12 months after issued_at.
"""
import json
import subprocess
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.agent.prompts import ANALYZER_SYSTEM_PROMPT
from app.ai.mock import MockAI
from app.ai.utils import AnalyzerResult, InterviewerResult, validate_json
from app.blueprints.loader import load_blueprint
from app.crypto.sign import sign_payload
from app.db import get_session
from app.main import app
from app.models import Attempt, Vouch, WitnessInvite, Worker, utc_now
from app.schemas import VouchCreate
from app.services.attempt_service import create_attempt
from app.services.witness_service import create_witness_invites, submit_vouch
from app.trust.score import check_safety_gate, video_score
from app.trust.tiers import calculate_tier, calculate_trust_score
from app.trust.weights import calculate_weight
from app.video.meta import extract_metadata
from tests.test_routers import get_test_session, test_engine

client = TestClient(app)


@pytest.fixture(autouse=True)
def ensure_db_override():
    app.dependency_overrides[get_session] = get_test_session
    yield


# ============================================================================
# 1. WebM Video Metadata Extraction
# ============================================================================
def test_webm_metadata_extraction(tmp_path):
    """Verify that .webm video metadata (duration, width, height, fps) is correctly parsed."""
    import imageio_ffmpeg

    exe = imageio_ffmpeg.get_ffmpeg_exe()
    webm_file = tmp_path / "test_sample.webm"

    # Generate a synthetic 3-second 640x480 30fps webm video using lavfi
    cmd = [
        exe,
        "-y",
        "-f",
        "lavfi",
        "-i",
        "testsrc=duration=3:size=640x480:rate=30",
        "-c:v",
        "libvpx-vp9",
        str(webm_file),
    ]
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    assert res.returncode == 0
    assert webm_file.exists()

    meta = extract_metadata(webm_file)
    assert meta["duration"] > 0
    assert meta["width"] == 640
    assert meta["height"] == 480
    assert meta["fps"] > 0
    assert meta["frame_count"] > 0


# ============================================================================
# 2. MockAI Rubber-stamping & Adversarial Trigger Rejection
# ============================================================================
def test_mock_ai_rejects_wet_pant_adversarial():
    """MockAI must return 'unclear' / score 0 when prompt contains 'my pant is wet'."""
    ai = MockAI()

    # Analyzer with adversarial phrase
    analyzer_res = ai.generate_content("Analyzer evaluation: worker says my pant is wet")
    parsed_analyzer = validate_json(analyzer_res, AnalyzerResult)
    for step in parsed_analyzer.steps:
        assert step.verdict == "unclear"
        assert step.confidence == 0.0
    assert parsed_analyzer.challenge_code_seen is False
    assert parsed_analyzer.video_quality.rating == "poor"

    # Interviewer with adversarial phrase
    interviewer_res = ai.generate_content(
        "Interviewer evaluation: answer was my pant is wet",
        system_instruction="You are an interviewer",
    )
    parsed_interviewer = validate_json(interviewer_res, InterviewerResult)
    assert parsed_interviewer.score == 0
    assert len(parsed_interviewer.missing_points) > 0


def test_mock_ai_rejects_unrecognized_input():
    """MockAI must return 'unclear' for completely off-topic / unrecognized inputs."""
    ai = MockAI()
    raw = ai.generate_content(
        "Analyzer: Step ID: step_cooking. Video shows chef frying pancakes in kitchen."
    )
    parsed = validate_json(raw, AnalyzerResult)
    for step in parsed.steps:
        assert step.verdict == "unclear"
        assert step.confidence == 0.0
    assert parsed.challenge_code_seen is False


def test_mock_ai_passes_recognized_blueprint_input():
    """MockAI returns 'pass' for valid recognized trade demonstrations."""
    ai = MockAI()
    raw = ai.generate_content(
        "Analyzer: visual criteria for electrician_socket Step ID: step_1. Step ID: step_2. wire MCB tester"
    )
    parsed = validate_json(raw, AnalyzerResult)
    assert len(parsed.steps) >= 2
    for step in parsed.steps:
        assert step.verdict == "pass"
        assert step.confidence >= 0.9
    assert parsed.challenge_code_seen is True


# ============================================================================
# 3. Deterministic Tier Engine Rules
# ============================================================================
def test_tier_rules_deterministic():
    # Tier 1 requires score >= 70, no fraud, critical pass, safety pass
    assert calculate_tier(70.0, True, False, False, 0.0) == 1
    assert calculate_tier(69.9, True, False, False, 0.0) == 0  # Below 70 threshold
    assert calculate_tier(85.0, False, False, False, 0.0) == 0  # Critical step failed
    assert calculate_tier(85.0, True, True, False, 0.0) == 0  # Fraud flag present

    # Tier 2 requires witness_weight >= 1.0
    assert calculate_tier(75.0, True, False, False, 1.0) == 2
    assert calculate_tier(75.0, True, False, False, 0.99) == 1

    # Tier 3 requires witness_weight >= 3.0 AND >= 2 distinct AND >= 1 trainer/employer
    assert calculate_tier(80.0, True, False, False, 3.0, distinct_witnesses=2, has_trainer_or_employer=True) == 3
    # Lacking trainer or employer caps at Tier 2
    assert calculate_tier(80.0, True, False, False, 3.5, distinct_witnesses=2, has_trainer_or_employer=False) == 2
    # Lacking 2 distinct witnesses caps at Tier 2
    assert calculate_tier(80.0, True, False, False, 3.5, distinct_witnesses=1, has_trainer_or_employer=True) == 2


# ============================================================================
# 4. N1 Safety Gate: Caps Video Score and Tier at 0
# ============================================================================
def test_safety_gate_caps_at_zero():
    # Step with safety_critical=True marked 'unclear'
    steps = [
        {"id": "s1", "verdict": "unclear", "critical": True, "safety_critical": True},
        {"id": "s2", "verdict": "pass", "critical": True, "safety_critical": False},
        {"id": "s3", "verdict": "pass", "critical": False, "safety_critical": False},
    ]
    passed, failed_ids = check_safety_gate(steps)
    assert passed is False
    assert "s1" in failed_ids

    # Video score is forced to 0.0 immediately
    score = video_score(steps)
    assert score == 0.0

    # Tier is forced to 0
    tier = calculate_tier(
        video_score=score,
        critical_steps_pass=True,
        has_fraud_flag=False,
        safety_gate_failed=True,
        witness_weight=3.5,
        distinct_witnesses=2,
        has_trainer_or_employer=True,
    )
    assert tier == 0


# ============================================================================
# 5. Duplicate Device Fingerprint Returns 0.0 Weight
# ============================================================================
def test_duplicate_device_fingerprint_zero_weight():
    # First witness on this device
    w1 = calculate_weight(
        role="peer",
        device_fp="device-fp-xyz",
        existing_vouch_device_fps=[],
    )
    assert w1 == 1.0

    # Second witness using same device fingerprint -> 0.0 weight
    w2 = calculate_weight(
        role="peer",
        device_fp="device-fp-xyz",
        existing_vouch_device_fps=["device-fp-xyz"],
    )
    assert w2 == 0.0

    # Case-insensitive duplicate check
    w3 = calculate_weight(
        role="peer",
        device_fp="DEVICE-FP-XYZ",
        existing_vouch_device_fps=["device-fp-xyz"],
    )
    assert w3 == 0.0


# ============================================================================
# 6. Witness Role Trust Hole & Downgrade to Peer
# ============================================================================
def test_witness_trainer_role_downgrades_without_code_or_credential():
    with Session(test_engine) as session:
        worker = Worker(name="Test Candidate", area="Bangalore", language="en", consent=True, token="tok-cand")
        session.add(worker)
        session.commit()
        session.refresh(worker)

        attempt = create_attempt(worker_id=worker.id, skill_id="electrician_socket", db=session)
        invites = create_witness_invites(attempt.id, count=2, db=session, base_url="http://localhost")
        token_unverified = invites[0]["token"]
        token_verified = invites[1]["token"]

        # Case A: Claims trainer role without institute code or credential -> downgraded to peer (weight 1.0)
        vouch_unverified = submit_vouch(
            token=token_unverified,
            vouch_data=VouchCreate(
                witness_name="Unverified Trainer",
                role="trainer",
                institute_code=None,
                has_credential=False,
                verdict="yes",
            ),
            db=session,
        )
        assert vouch_unverified.role == "peer"
        assert vouch_unverified.weight == 1.0

        # Case B: Claims trainer role WITH valid institute code SAKSHI2026 -> trainer role and 1.5 weight
        vouch_verified = submit_vouch(
            token=token_verified,
            vouch_data=VouchCreate(
                witness_name="Verified Trainer",
                role="trainer",
                institute_code="SAKSHI2026",
                verdict="yes",
            ),
            db=session,
        )
        assert vouch_verified.role == "trainer"
        assert vouch_verified.weight == 1.5


# ============================================================================
# 7. Canonical Payload Contains 'valid_until' (12 months validity)
# ============================================================================
def test_canonical_payload_has_valid_until():
    with Session(test_engine) as session:
        worker = Worker(name="Cred Worker", area="Bangalore", language="en", consent=True, token="tok-c")
        session.add(worker)
        session.commit()
        session.refresh(worker)

        attempt = create_attempt(worker_id=worker.id, skill_id="plumber_joint", db=session)
        attempt.status = "reviewed"
        attempt.video_score = 85.0
        session.add(attempt)
        session.commit()

        # Finalize credential
        res = client.post(f"/api/attempts/{attempt.id}/finalize")
        assert res.status_code == 200
        data = res.json()["data"]

        # Payload must include valid_until
        payload = data["payload"]
        assert "valid_until" in payload
        assert "issued_at" in payload

        issued_dt = datetime.fromisoformat(payload["issued_at"])
        valid_until_dt = datetime.fromisoformat(payload["valid_until"])

        # Difference should be approx 365 days
        delta = valid_until_dt - issued_dt
        assert 364 <= delta.days <= 366
