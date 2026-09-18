from __future__ import annotations

from fastapi.testclient import TestClient


def test_configured_frontend_origin_receives_authorization_cors_headers(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "resume.db"))
    monkeypatch.setenv("TEMP_FILE_PATH", str(tmp_path / "temp"))
    monkeypatch.setenv("CORS_ORIGINS", "https://dashboard.example.com")

    from main import create_app

    with TestClient(create_app()) as client:
        response = client.options(
            "/api/draft/list",
            headers={
                "Origin": "https://dashboard.example.com",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "authorization",
            },
        )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://dashboard.example.com"
    assert "Authorization" in response.headers["access-control-allow-headers"]


def test_quoted_csv_entries_are_stripped(tmp_path, monkeypatch):
    """控制台粘贴环境值时常见的引号包裹不应让整条白名单失效。"""
    from app.config import _read_csv

    monkeypatch.setenv("CORS_ORIGINS", '"https://a.example.com", https://b.example.com ')
    assert _read_csv("CORS_ORIGINS") == ("https://a.example.com", "https://b.example.com")
