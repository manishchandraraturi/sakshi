import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

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


def test_create_witness_invites_flow():
    with Session(test_engine) as session:
        # Create a test worker & attempt
        worker = Worker(
            name="Ramesh Sharma",
            language="hi",
            area="Delhi West",
            token="tok_ramesh",
            device_fp="fp_worker_1",
        )
        session.add(worker)
        session.commit()
        session.refresh(worker)

        attempt = create_attempt(worker.id, "electrician_socket", session)
        attempt_id = attempt.id

    # 1. Generate 3 witness invites
    res = client.post(
        f"/api/attempts/{attempt_id}/witnesses",
        json={"count": 3},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert len(body["data"]) == 3
    for inv in body["data"]:
        assert "token" in inv
        assert "url" in inv
        assert f"/w/{inv['token']}" in inv["url"]

    # Verify attempt status transitioned to awaiting_witnesses
    with Session(test_engine) as session:
        refreshed_attempt = session.exec(
            select(Attempt).where(Attempt.id == attempt_id)
        ).first()
        assert refreshed_attempt.status == "awaiting_witnesses"


def test_create_witness_invites_invalid_attempt():
    res = client.post(
        "/api/attempts/non_existent_attempt_id/witnesses",
        json={"count": 2},
    )
    assert res.status_code == 404
    body = res.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "ATTEMPT_NOT_FOUND"


def test_witness_page_retrieval_and_vouch_submission():
    with Session(test_engine) as session:
        worker = Worker(
            name="Suresh Raina",
            language="hi",
            area="Kanpur",
            token="tok_suresh",
            device_fp="fp_worker_suresh",
        )
        session.add(worker)
        session.commit()
        session.refresh(worker)

        attempt = create_attempt(worker.id, "plumber_joint", session)
        attempt_id = attempt.id

    # Generate an invite
    res_invites = client.post(
        f"/api/attempts/{attempt_id}/witnesses",
        json={"count": 1},
    )
    assert res_invites.status_code == 200
    token = res_invites.json()["data"][0]["token"]

    # 1. Fetch witness page
    res_page = client.get(f"/api/w/{token}")
    assert res_page.status_code == 200
    page_data = res_page.json()["data"]
    assert page_data["worker_first_name"] == "Suresh"
    assert "Pipe joint" in page_data["skill"]
    assert len(page_data["steps"]) >= 4

    # 2. Submit vouch as trainer with valid institute code
    res_vouch = client.post(
        f"/api/w/{token}/vouch",
        json={
            "witness_name": "Master Mason Gupta",
            "role": "trainer",
            "institute_code": "SAKSHI2026",
            "seen_in_person": True,
            "known_years_bucket": "3+",
            "would_hire": True,
            "verdict": "yes",
            "device_fp": "fp_witness_trainer",
        },
    )
    assert res_vouch.status_code == 200
    vouch_body = res_vouch.json()
    assert vouch_body["ok"] is True
    assert vouch_body["data"]["weight"] == 1.5  # trainer base weight = 1.5
    assert vouch_body["data"]["status"] == "recorded"

    # 3. Verify invite token is now consumed (subsequent get returns 400 INVITE_ALREADY_USED)
    res_page_after = client.get(f"/api/w/{token}")
    assert res_page_after.status_code == 400
    assert res_page_after.json()["error"]["code"] == "INVITE_ALREADY_USED"

    # 4. Verify duplicate submit on same token returns 400 INVITE_ALREADY_USED
    res_vouch_dup = client.post(
        f"/api/w/{token}/vouch",
        json={
            "witness_name": "Another Person",
            "role": "peer",
            "verdict": "yes",
        },
    )
    assert res_vouch_dup.status_code == 400
    assert res_vouch_dup.json()["error"]["code"] == "INVITE_ALREADY_USED"


def test_witness_vouch_anti_fraud_rules():
    with Session(test_engine) as session:
        worker = Worker(
            name="Vikram Seth",
            language="kn",
            area="Bangalore South",
            token="tok_vikram",
            device_fp="fp_vikram_device",
        )
        session.add(worker)
        session.commit()
        session.refresh(worker)

        attempt = create_attempt(worker.id, "mason_wall", session)
        attempt_id = attempt.id

    # Create 4 invites for this attempt
    res_invites = client.post(
        f"/api/attempts/{attempt_id}/witnesses",
        json={"count": 4},
    )
    tokens = [inv["token"] for inv in res_invites.json()["data"]]

    # Case A: Same device as worker -> weight must be 0.0
    res_a = client.post(
        f"/api/w/{tokens[0]}/vouch",
        json={
            "witness_name": "Self or Buddy on same phone",
            "role": "trainer",
            "verdict": "yes",
            "device_fp": "fp_vikram_device",  # same device fingerprint as worker
        },
    )
    assert res_a.status_code == 200
    assert res_a.json()["data"]["weight"] == 0.0

    # Case B: First valid witness on distinct phone -> weight is normal
    res_b = client.post(
        f"/api/w/{tokens[1]}/vouch",
        json={
            "witness_name": "Anil Colleague",
            "role": "peer",
            "verdict": "yes",
            "device_fp": "fp_phone_peer_1",
        },
    )
    assert res_b.status_code == 200
    assert res_b.json()["data"]["weight"] == 1.0

    # Case C: Duplicate witness device fingerprint for this attempt -> only first counts (weight 0.0)
    res_c = client.post(
        f"/api/w/{tokens[2]}/vouch",
        json={
            "witness_name": "Different Name Same Phone",
            "role": "peer",
            "verdict": "yes",
            "device_fp": "fp_phone_peer_1",  # duplicate device
        },
    )
    assert res_c.status_code == 200
    assert res_c.json()["data"]["weight"] == 0.0

    # Case D: Verdict 'needs_work' -> weight is 0.0
    res_d = client.post(
        f"/api/w/{tokens[3]}/vouch",
        json={
            "witness_name": "Strict Trainer",
            "role": "trainer",
            "verdict": "needs_work",
            "device_fp": "fp_phone_trainer_strict",
        },
    )
    assert res_d.status_code == 200
    assert res_d.json()["data"]["weight"] == 0.0


def test_witness_vouch_reciprocity_and_credential():
    with Session(test_engine) as session:
        # Worker 1 (Dev)
        w1 = Worker(
            name="Devendra Yadav",
            language="hi",
            area="Noida",
            token="tok_w1",
            device_fp="fp_w1",
        )
        # Worker 2 (Pankaj)
        w2 = Worker(
            name="Pankaj Tripathi",
            language="hi",
            area="Noida",
            token="tok_w2",
            device_fp="fp_w2",
        )
        session.add(w1)
        session.add(w2)
        session.commit()
        session.refresh(w1)
        session.refresh(w2)

        # Pankaj has an existing credential
        cred = Credential(
            attempt_id="dummy_attempt",
            worker_id=w2.id,
            skill_id="electrician_socket",
            tier=2,
            trust_score=85.0,
            payload_json="{}",
            signature_b64="dGVzdA==",
            evidence_sha256="abc",
            revoked=False,
        )
        session.add(cred)

        # Devendra had previously vouched on an attempt by Pankaj (creates reciprocity)
        attempt_pankaj = create_attempt(w2.id, "electrician_socket", session)
        dummy_invite = WitnessInvite(attempt_id=attempt_pankaj.id, token="tok_dummy_inv")
        session.add(dummy_invite)
        session.commit()
        session.refresh(dummy_invite)

        prior_vouch = Vouch(
            invite_id=dummy_invite.id,
            attempt_id=attempt_pankaj.id,
            witness_name="Devendra Yadav",  # Devendra vouched for Pankaj!
            role="peer",
            known_years_bucket="1-3",
            verdict="yes",
            weight=1.0,
        )
        session.add(prior_vouch)
        session.commit()

        # Now Devendra creates an attempt, and Pankaj vouches for Devendra
        attempt_dev = create_attempt(w1.id, "electrician_socket", session)
        attempt_dev_id = attempt_dev.id

    res_inv = client.post(f"/api/attempts/{attempt_dev_id}/witnesses", json={"count": 1})
    token = res_inv.json()["data"][0]["token"]

    # Pankaj vouches for Devendra
    # Role = peer (base 1.0)
    # Pankaj has credential: x 1.5
    # Reciprocal (Devendra vouched for Pankaj earlier): x 0.5
    # Result: 1.0 * 1.5 * 0.5 = 0.75
    res_vouch = client.post(
        f"/api/w/{token}/vouch",
        json={
            "witness_name": "Pankaj Tripathi",
            "role": "peer",
            "seen_in_person": True,
            "verdict": "yes",
            "device_fp": "fp_w2",
        },
    )
    assert res_vouch.status_code == 200
    assert res_vouch.json()["data"]["weight"] == 0.75
