from __future__ import annotations

from fastapi.testclient import TestClient

from app.db import connect


def test_all_api_responses_include_request_id(api_client):
    healthy = api_client.get("/health")
    missing = api_client.get("/api/not-a-real-route")

    assert healthy.status_code == 200
    assert missing.status_code == 404
    assert healthy.headers["x-request-id"]
    assert missing.headers["x-request-id"]


def test_public_auth_endpoints_are_rate_limited(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "rate-limit.db"))
    monkeypatch.setenv("TEMP_FILE_PATH", str(tmp_path / "exports"))
    monkeypatch.setenv("AUTH_DEMO_MODE", "true")
    monkeypatch.setenv("JWT_SECRET", "test-jwt-secret-for-authentication")
    monkeypatch.setenv("AUTH_RATE_LIMIT_MAX_REQUESTS", "2")
    monkeypatch.setenv("AUTH_RATE_LIMIT_WINDOW_SECONDS", "60")

    from main import create_app

    with TestClient(create_app()) as client:
        payload = {"phone": "13800138000"}
        assert client.post("/api/auth/send-code", json=payload).status_code == 200
        assert client.post("/api/auth/send-code", json=payload).status_code == 200
        limited = client.post("/api/auth/send-code", json=payload)

    assert limited.status_code == 429
    assert limited.json()["code"] == "rate_limited"
    assert limited.headers["retry-after"] == "60"
    assert limited.headers["x-request-id"]


def test_sqlite_connection_uses_configured_busy_timeout(tmp_path):
    with connect(tmp_path / "resume.db", timeout_seconds=0.2) as connection:
        timeout = connection.execute("PRAGMA busy_timeout").fetchone()[0]

    assert timeout == 200
