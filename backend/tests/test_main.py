from fastapi.testclient import TestClient
from app.config import settings
from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["error"] is None
    assert body["data"]["status"] == "healthy"
    assert body["data"]["demo_mode"] == settings.DEMO_MODE
