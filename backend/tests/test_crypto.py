import json
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.crypto.sign import (
    canonical_json,
    get_or_create_keypair,
    get_public_key_b64,
    sign_payload,
    verify_signature,
)
from app.db import get_session
from app.main import app
from app.models import Attempt, Credential, Vouch, WitnessInvite, Worker
from app.services.attempt_service import create_attempt
from tests.test_routers import get_test_session, test_engine

client = TestClient(app)


@pytest.fixture(autouse=True)
def ensure_db_override():
    app.dependency_overrides[get_session] = get_test_session
    yield


# --- Unit Tests for Crypto Signing & Tamper Detection ---
def test_keypair_generation_and_pubkey():
    sk, vk = get_or_create_keypair()
    assert sk is not None
    assert vk is not None

    pubkey_b64 = get_public_key_b64()
    assert len(pubkey_b64) > 0


def test_canonical_json_deterministic_ordering():
    dict1 = {"b": 2, "a": 1, "c": {"y": "yes", "x": "no"}}
    dict2 = {"c": {"x": "no", "y": "yes"}, "a": 1, "b": 2}
    assert canonical_json(dict1) == canonical_json(dict2)
    assert canonical_json(dict1) == b'{"a":1,"b":2,"c":{"x":"no","y":"yes"}}'


def test_sign_and_verify_valid_payload():
    payload = {
        "cred_id": "test-cred-123",
        "worker_name": "Ravi Kumar",
        "skill": "Socket wiring",
        "tier": 2,
        "trust_score": 82.5,
    }
    sig_b64, pubkey_b64 = sign_payload(payload)
    assert len(sig_b64) > 0
    assert len(pubkey_b64) > 0

    # Verification with explicit pubkey
    is_valid = verify_signature(payload, sig_b64, pubkey_b64)
    assert is_valid is True

    # Verification with default server pubkey
    assert verify_signature(payload, sig_b64) is True


def test_tamper_detection_fails_verification():
    original_payload = {
        "cred_id": "test-cred-123",
        "worker_name": "Ravi Kumar",
        "tier": 2,
        "trust_score": 82.5,
    }
    sig_b64, pubkey_b64 = sign_payload(original_payload)

    # Tamper 1: Modify a field value (e.g. elevate tier from 2 to 3)
    tampered_payload_1 = dict(original_payload)
    tampered_payload_1["tier"] = 3
    assert verify_signature(tampered_payload_1, sig_b64, pubkey_b64) is False

    # Tamper 2: Alter worker name
    tampered_payload_2 = dict(original_payload)
    tampered_payload_2["worker_name"] = "Ravi Sharma"
    assert verify_signature(tampered_payload_2, sig_b64, pubkey_b64) is False

    # Tamper 3: Corrupt signature
    corrupt_sig = sig_b64[:-4] + "AAAA"
    assert verify_signature(original_payload, corrupt_sig, pubkey_b64) is False


# --- Integration Tests for Finalize & Credential Router ---
def test_finalize_attempt_and_issue_credential():
    with Session(test_engine) as session:
        # Create worker
        worker = Worker(
            name="Manoj Tiwari",
            language="hi",
            area="Patna",
            token="tok_manoj",
            device_fp="fp_manoj",
        )
        session.add(worker)
        session.commit()
        session.refresh(worker)

        # Create attempt with video evaluation
        attempt = create_attempt(worker.id, "electrician_socket", session)
        attempt.video_score = 85.0
        attempt.interview_score = 90.0
        attempt.status = "awaiting_witnesses"
        session.add(attempt)
        session.commit()
        session.refresh(attempt)
        attempt_id = attempt.id

        # Add 2 vouches (Trainer with weight 1.5, Peer with weight 1.0 -> total 2.5)
        inv1 = WitnessInvite(attempt_id=attempt_id, token="tok_inv_1")
        inv2 = WitnessInvite(attempt_id=attempt_id, token="tok_inv_2")
        session.add(inv1)
        session.add(inv2)
        session.commit()
        session.refresh(inv1)
        session.refresh(inv2)

        vouch1 = Vouch(
            invite_id=inv1.id,
            attempt_id=attempt_id,
            witness_name="Trainer Ramesh",
            role="trainer",
            known_years_bucket="3+",
            would_hire=True,
            verdict="yes",
            weight=1.5,
        )
        vouch2 = Vouch(
            invite_id=inv2.id,
            attempt_id=attempt_id,
            witness_name="Peer Suresh",
            role="peer",
            known_years_bucket="1-3",
            would_hire=True,
            verdict="yes",
            weight=1.0,
        )
        session.add(vouch1)
        session.add(vouch2)
        session.commit()

    # 1. Finalize attempt
    res = client.post(f"/api/attempts/{attempt_id}/finalize")
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    cred_data = body["data"]

    assert "credential_id" in cred_data
    # Weight 2.5 -> Tier 2 (since weight >= 1.0 but < 3.0)
    assert cred_data["tier"] == 2
    assert cred_data["trust_score"] > 0
    assert "signature" in cred_data
    assert cred_data["payload"]["worker_name"] == "Manoj Tiwari"

    # Verify signature matches payload
    sig = cred_data["signature"]
    payload = cred_data["payload"]
    assert verify_signature(payload, sig) is True

    # Verify DB attempt status is now finalized
    with Session(test_engine) as session:
        ref_attempt = session.exec(select(Attempt).where(Attempt.id == attempt_id)).first()
        assert ref_attempt.status == "finalized"

    # 2. Idempotency test: calling finalize again returns existing credential
    res_idempotent = client.post(f"/api/attempts/{attempt_id}/finalize")
    assert res_idempotent.status_code == 200
    body_idem = res_idempotent.json()
    assert body_idem["data"]["credential_id"] == cred_data["credential_id"]

    # 3. Fetch credential via GET /api/credentials/{id}
    res_get = client.get(f"/api/credentials/{cred_data['credential_id']}")
    assert res_get.status_code == 200
    get_data = res_get.json()["data"]
    assert get_data["credential_id"] == cred_data["credential_id"]
    assert get_data["tier"] == 2
    assert "pubkey" in get_data


def test_get_public_key_endpoint():
    res = client.get("/api/pubkey")
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert "pubkey" in body["data"]
    assert len(body["data"]["pubkey"]) > 0
