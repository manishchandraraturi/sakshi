import json
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.crypto.sign import sign_payload
from app.db import get_session
from app.main import app
from app.models import Credential, Worker, utc_now
from tests.test_routers import get_test_session, test_engine

client = TestClient(app)


@pytest.fixture(autouse=True)
def ensure_db_override():
    app.dependency_overrides[get_session] = get_test_session
    yield


@pytest.fixture(scope="module")
def setup_directory_workers():
    """
    Sets up 3 active credentials across different trades/areas,
    plus 1 revoked credential.
    """
    now = utc_now()
    with Session(test_engine) as session:
        # Worker 1: Electrician in Bangalore South
        w1 = Worker(
            name="Ravi Kumar Test",
            language="kn",
            area="Bangalore South",
            token="tok_w1",
        )
        # Worker 2: Mason in Delhi West
        w2 = Worker(
            name="Suresh Patil Test",
            language="hi",
            area="Delhi West",
            token="tok_w2",
        )
        # Worker 3: Plumber in Bangalore North
        w3 = Worker(
            name="Anita Sharma Test",
            language="hi",
            area="Bangalore North",
            token="tok_w3",
        )
        # Worker 4: Revoked Painter in Mumbai
        w4 = Worker(
            name="Revoked Worker",
            language="hi",
            area="Mumbai Central",
            token="tok_w4",
        )
        session.add(w1)
        session.add(w2)
        session.add(w3)
        session.add(w4)
        session.commit()
        session.refresh(w1)
        session.refresh(w2)
        session.refresh(w3)
        session.refresh(w4)

        # Helper to create and sign credentials
        def make_cred(worker, trade, skill, tier, score, revoked=False):
            cid = str(uuid.uuid4())
            payload = {
                "cred_id": cid,
                "worker_name": worker.name,
                "area": worker.area,
                "trade": trade,
                "skill": skill,
                "tier": tier,
                "trust_score": score,
                "issued_at": now.isoformat(),
                "evidence_sha256": "none",
                "witness_count": 1,
            }
            sig, _ = sign_payload(payload)
            cred = Credential(
                id=cid,
                attempt_id=f"att_{cid[:8]}",
                worker_id=worker.id,
                skill_id=skill,
                tier=tier,
                trust_score=float(score),
                payload_json=json.dumps(payload, sort_keys=True, separators=(",", ":")),
                signature_b64=sig,
                evidence_sha256="none",
                issued_at=now,
                revoked=revoked,
            )
            session.add(cred)
            return cred

        c1 = make_cred(w1, "Electrician", "Socket wiring", 3, 92)
        c2 = make_cred(w2, "Mason", "Wall alignment", 2, 78)
        c3 = make_cred(w3, "Plumber", "Pipe joint test", 1, 71)
        c4 = make_cred(w4, "Painter", "Wall painting", 1, 60, revoked=True)
        session.commit()

        return {
            "electrician": (w1, c1),
            "mason": (w2, c2),
            "plumber": (w3, c3),
            "revoked": (w4, c4),
        }


def test_list_directory_all(setup_directory_workers):
    res = client.get("/api/directory")
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    data = body["data"]

    # Must contain the 3 active workers (excluding revoked)
    names = [item["name"] for item in data]
    assert "Ravi Kumar Test" in names
    assert "Suresh Patil Test" in names
    assert "Anita Sharma Test" in names
    assert "Revoked Worker" not in names


def test_list_directory_filter_trade(setup_directory_workers):
    # Filter by Electrician
    res_elec = client.get("/api/directory?trade=Electrician")
    assert res_elec.status_code == 200
    data_elec = res_elec.json()["data"]
    assert all("electrician" in item["trade"].lower() for item in data_elec)
    assert any(item["name"] == "Ravi Kumar Test" for item in data_elec)

    # Filter by Plumber
    res_plumb = client.get("/api/directory?trade=Plumber")
    assert res_plumb.status_code == 200
    data_plumb = res_plumb.json()["data"]
    assert all("plumber" in item["trade"].lower() for item in data_plumb)
    assert any(item["name"] == "Anita Sharma Test" for item in data_plumb)

    # Non-existent trade
    res_none = client.get("/api/directory?trade=Welder")
    assert res_none.status_code == 200
    assert len(res_none.json()["data"]) == 0


def test_list_directory_filter_area(setup_directory_workers):
    # Filter by Bangalore
    res_blr = client.get("/api/directory?area=Bangalore")
    assert res_blr.status_code == 200
    data_blr = res_blr.json()["data"]
    assert len(data_blr) >= 2
    assert all("bangalore" in item["area"].lower() for item in data_blr)

    # Filter by Delhi
    res_delhi = client.get("/api/directory?area=Delhi")
    assert res_delhi.status_code == 200
    data_delhi = res_delhi.json()["data"]
    assert any(item["name"] == "Suresh Patil Test" for item in data_delhi)


def test_list_directory_filter_trade_and_area(setup_directory_workers):
    # Plumber in Bangalore -> Matches Anita
    res_match = client.get("/api/directory?trade=Plumber&area=Bangalore")
    assert res_match.status_code == 200
    data_match = res_match.json()["data"]
    assert len(data_match) >= 1
    assert all("plumber" in item["trade"].lower() for item in data_match)
    assert all("bangalore" in item["area"].lower() for item in data_match)
    assert all(item["name"] == "Anita Sharma Test" for item in data_match)

    # Plumber in Delhi -> No match
    res_nomatch = client.get("/api/directory?trade=Plumber&area=Delhi")
    assert res_nomatch.status_code == 200
    assert len(res_nomatch.json()["data"]) == 0
