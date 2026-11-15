import os
os.environ.setdefault("DATABASE_PATH", "/tmp/ai-shorts-factory-test.db")
os.environ.setdefault("OUTPUT_DIR", "/tmp/ai-shorts-factory-test-output")

from fastapi.testclient import TestClient
import app.main as main


def test_health_is_public():
    client = TestClient(main.app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_jobs_require_api_key(monkeypatch):
    monkeypatch.setattr(main, "API_KEY", "test-secret")
    client = TestClient(main.app)
    assert client.get("/api/jobs").status_code == 401
    response = client.get("/api/jobs", headers={"Authorization": "Bearer test-secret"})
    assert response.status_code == 200


def test_api_fails_closed_without_key(monkeypatch):
    monkeypatch.setattr(main, "API_KEY", "")
    client = TestClient(main.app)
    response = client.get("/api/jobs")
    assert response.status_code == 503
