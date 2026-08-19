from __future__ import annotations

from fastapi.testclient import TestClient

from main import create_app


def test_phase6_phone_login_protects_business_routes_and_handles_expired_session(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "phase6-auth.db"))
    monkeypatch.setenv("TEMP_FILE_PATH", str(tmp_path / "exports"))
    monkeypatch.setenv("AUTH_DEMO_MODE", "true")
    monkeypatch.setenv("JWT_SECRET", "phase6-auth-test-secret-with-32-bytes")

    with TestClient(create_app()) as client:
        sent = client.post("/api/auth/send-code", json={"phone": "13800138000"})
        assert sent.status_code == 200
        assert sent.json()["data"]["demo_code"] == "123456"

        login = client.post(
            "/api/auth/login-phone",
            json={"phone": "13800138000", "code": "123456"},
        )
        assert login.status_code == 200
        token = login.json()["data"]["token"]
        user_id = login.json()["data"]["user"]["user_id"]
        headers = {"Authorization": f"Bearer {token}"}

        protected = client.get("/api/template/list", headers=headers)
        assert protected.status_code == 200

        client.app.state.user_repository.invalidate_tokens(user_id)
        expired = client.get("/api/template/list", headers=headers)
        assert expired.status_code == 401
        assert expired.json()["code"] == "unauthorized"

        logout = client.post("/api/auth/logout")
        assert logout.status_code == 200
        assert logout.json()["data"]["logged_out"] is True
