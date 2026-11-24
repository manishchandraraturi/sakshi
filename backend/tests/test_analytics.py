import json
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.db import get_session
from app.main import app
from app.models import Credential, Vouch, Worker, WitnessInvite, utc_now
from tests.test_routers import get_test_session, test_engine

client = TestClient(app)


@pytest.fixture(autouse=True)
def ensure_db_override():
    app.dependency_overrides[get_session] = get_test_session
    yield


def test_directory_analytics_endpoint():
    now = utc_now()
    tag = uuid.uuid4().hex[:6]

    with Session(test_engine) as session:
        # 1. Create workers (use distinct areas not colliding with test_directory)
        w1 = Worker(
            name=f"Analytics Worker 1 {tag}",
            language="en",
            area="Pune",
            token=f"tok_an1_{tag}",
        )
        w2 = Worker(
            name=f"Analytics Worker 2 {tag}",
            language="hi",
            area="Nagpur",
            token=f"tok_an2_{tag}",
        )
        w3 = Worker(
            name=f"Analytics Worker 3 {tag}",
            language="kn",
            area="Mysore",
            token=f"tok_an3_{tag}",
        )
        session.add(w1)
        session.add(w2)
        session.add(w3)
        session.commit()
        session.refresh(w1)
        session.refresh(w2)
        session.refresh(w3)

        # 2. Create active credentials
        c1 = Credential(
            id=f"cred_an1_{tag}",
            attempt_id=f"att_an1_{tag}",
            worker_id=w1.id,
            skill_id="electrician_wiring",
            tier=1,
            trust_score=75.0,
            payload_json=json.dumps({"trade": "Electrician", "worker_name": w1.name}),
            signature_b64="sig1",
            evidence_sha256="sha1",
            issued_at=now,
            revoked=False,
        )
        c2 = Credential(
            id=f"cred_an2_{tag}",
            attempt_id=f"att_an2_{tag}",
            worker_id=w2.id,
            skill_id="plumber_joint",
            tier=2,
            trust_score=85.0,
            payload_json=json.dumps({"trade": "Plumber", "worker_name": w2.name}),
            signature_b64="sig2",
            evidence_sha256="sha2",
            issued_at=now,
            revoked=False,
        )
        c3 = Credential(
            id=f"cred_an3_{tag}",
            attempt_id=f"att_an3_{tag}",
            worker_id=w3.id,
            skill_id="mason_wall",
            tier=3,
            trust_score=95.0,
            payload_json=json.dumps({"trade": "Mason", "worker_name": w3.name}),
            signature_b64="sig3",
            evidence_sha256="sha3",
            issued_at=now,
            revoked=False,
        )
        # Revoked credential should be excluded from active tiers/trades
        c_rev = Credential(
            id=f"cred_an_rev_{tag}",
            attempt_id=f"att_an_rev_{tag}",
            worker_id=w1.id,
            skill_id="welder_pipe",
            tier=2,
            trust_score=80.0,
            payload_json=json.dumps({"trade": "Welder"}),
            signature_b64="sig_rev",
            evidence_sha256="sha_rev",
            issued_at=now,
            revoked=True,
        )
        session.add(c1)
        session.add(c2)
        session.add(c3)
        session.add(c_rev)

        # 3. Create vouches
        v1 = Vouch(
            invite_id=f"inv1_{tag}",
            attempt_id=f"att_an2_{tag}",
            witness_name="Test Witness 1",
            role="colleague",
            known_years_bucket="2-5",
            verdict="yes",
            weight=1.0,
        )
        v2 = Vouch(
            invite_id=f"inv2_{tag}",
            attempt_id=f"att_an3_{tag}",
            witness_name="Test Witness 2",
            role="employer",
            known_years_bucket="5+",
            verdict="yes",
            weight=2.0,
        )
        session.add(v1)
        session.add(v2)
        session.commit()

    # Query analytics API
    res = client.get("/api/directory/analytics")
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["error"] is None

    data = body["data"]
    assert "total_workers" in data
    assert data["total_workers"] >= 3

    assert "tier_distribution" in data
    tier_dist = data["tier_distribution"]
    assert "tier_1" in tier_dist
    assert "tier_2" in tier_dist
    assert "tier_3" in tier_dist
    assert tier_dist["tier_1"] >= 1
    assert tier_dist["tier_2"] >= 1
    assert tier_dist["tier_3"] >= 1

    assert "trade_distribution" in data
    trade_dist = data["trade_distribution"]
    assert "electrician" in trade_dist
    assert "plumber" in trade_dist
    assert "mason" in trade_dist
    assert trade_dist["electrician"] >= 1
    assert trade_dist["plumber"] >= 1
    assert trade_dist["mason"] >= 1

    assert "total_vouches" in data
    assert data["total_vouches"] >= 2
