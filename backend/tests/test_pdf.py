import json
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.crypto.pdf import generate_pdf
from app.db import get_session
from app.main import app
from app.models import Credential, utc_now
from tests.test_routers import test_engine


def test_generate_pdf_unit():
    payload = {
        "cred_id": "test-cred-unit-001",
        "worker_name": "Ramesh Kumar",
        "area": "Dharavi, Mumbai",
        "trade": "Plumbing",
        "skill": "Pipe Joint & Sealing",
        "tier": 2,
        "trust_score": 85,
        "witness_count": 3,
        "evidence_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "issued_at": utc_now().isoformat(),
        "valid_until": utc_now().isoformat(),
    }
    pdf_bytes = generate_pdf(payload)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF-")


def test_generate_pdf_unicode_and_edge_cases():
    payload = {
        "cred_id": "test-cred-unicode-002",
        "worker_name": "Rámesh Kumär — “Master” Plumber",
        "area": "Sector 5, Salt Lake, Kolkata",
        "trade": "Welder",
        "skill": "Pipe Welding & Joint Integrity",
        "tier": 3,
        "trust_score": 95,
        "witness_count": 0,
    }
    pdf_bytes = generate_pdf(payload)
    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF-")


def test_get_credential_pdf_route_404():
    client = TestClient(app)
    res = client.get("/api/credentials/non-existent-id/pdf")
    assert res.status_code == 404
    data = res.json()
    assert data["ok"] is False
    assert data["error"]["code"] == "CREDENTIAL_NOT_FOUND"


def test_get_credential_pdf_route_success():
    client = TestClient(app)
    cred_id = "test-pdf-route-cred"

    payload = {
        "cred_id": cred_id,
        "worker_name": "Sunita Sharma",
        "area": "Andheri East, Mumbai",
        "trade": "Electrical",
        "skill": "Three-Phase Distribution",
        "tier": 2,
        "trust_score": 88,
        "witness_count": 2,
    }

    with Session(test_engine) as session:
        cred = session.exec(select(Credential).where(Credential.id == cred_id)).first()
        if not cred:
            cred = Credential(
                id=cred_id,
                attempt_id="att-test-pdf",
                worker_id="w-test-pdf",
                skill_id="electrician_wiring",
                tier=2,
                trust_score=88.0,
                payload_json=json.dumps(payload),
                signature_b64="mock_signature",
                evidence_sha256="mock_hash",
                issued_at=utc_now(),
                revoked=False,
            )
            session.add(cred)
            session.commit()

    res = client.get(f"/api/credentials/{cred_id}/pdf")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert f'filename="credential_{cred_id}.pdf"' in res.headers.get("content-disposition", "")
    assert res.content.startswith(b"%PDF-")
