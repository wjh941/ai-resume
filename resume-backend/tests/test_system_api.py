from __future__ import annotations

from dataclasses import replace

from fastapi.testclient import TestClient

def test_health_declares_current_dashboard_capabilities(api_client):
    response = api_client.get("/health")

    assert response.status_code == 200
    assert {"job_plan", "job_match", "ai_setup"} <= set(response.json()["data"]["capabilities"])


def test_health_detail_reports_database_and_storage_readiness(api_client):
    response = api_client.get("/api/system/health-detail")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "healthy"
    assert data["database"]["status"] == "connected"
    assert data["storage"]["status"] == "ready"


def test_ai_status_hides_secrets_and_declares_local_setup_availability(api_client):
    response = api_client.get("/api/system/ai-status")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["configured"] is False
    assert data["setup_allowed"] is True
    assert "api_key" not in data


def test_ai_config_rejects_when_local_setup_is_disabled(api_client):
    api_client.app.state.settings = replace(
        api_client.app.state.settings, ai_config_ui_enabled=False
    )
    response = api_client.post(
        "/api/system/ai-config",
        json={
            "provider": "openai_compatible",
            "base_url": "https://api.example.test/v1",
            "api_key": "test-secret",
            "model": "test-model",
        },
    )

    assert response.status_code == 403


def test_ai_config_accepts_loopback_development_requests_without_returning_secret(
    api_client, tmp_path
):
    api_client.app.state.ai_config_path = tmp_path / ".env"
    with TestClient(api_client.app, client=("127.0.0.1", 50100)) as local_client:
        local_client.headers.update(api_client.headers)
        response = local_client.post(
            "/api/system/ai-config",
            json={
                "provider": "openai_compatible",
                "base_url": "https://api.example.test/v1",
                "api_key": "test-secret",
                "model": "test-model",
            },
        )

    assert response.status_code == 200
    assert response.json()["data"]["configured"] is True
    assert "test-secret" not in response.text
    assert "AI_API_KEY=test-secret" in (tmp_path / ".env").read_text(encoding="utf-8")
