from __future__ import annotations

import sqlite3
from io import StringIO
from pathlib import Path

import jwt
from alembic import command
from alembic.config import Config
from fastapi import Depends
from fastapi.testclient import TestClient

from app.config import load_settings
from app.db import initialize_database


BACKEND_ROOT = Path(__file__).resolve().parents[1]


def _upgrade(url: str, revision: str = "head") -> None:
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", url)
    command.upgrade(config, revision)


def _client(monkeypatch, tmp_path, allowlist: str = "") -> TestClient:
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "phase10.db"))
    monkeypatch.setenv("TEMP_FILE_PATH", str(tmp_path / "temp"))
    monkeypatch.setenv("AUTH_DEMO_MODE", "true")
    monkeypatch.setenv("JWT_SECRET", "phase10-rbac-secret-at-least-thirty-two-bytes")
    monkeypatch.setenv("OPERATOR_PHONE_ALLOWLIST", allowlist)
    from main import create_app

    return TestClient(create_app())


def test_operator_allowlist_login_persists_role_and_signs_claim(monkeypatch, tmp_path):
    with _client(monkeypatch, tmp_path, " 13800138000 ") as client:
        response = client.post(
            "/api/auth/login-phone", json={"phone": "138 00138000", "code": "123456"}
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["user"]["role"] == "operator"
        assert jwt.decode(data["token"], "phase10-rbac-secret-at-least-thirty-two-bytes", algorithms=["HS256"])["role"] == "operator"
        assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {data['token']}"}).json()["data"]["role"] == "operator"

    with _client(monkeypatch, tmp_path) as client:
        response = client.post(
            "/api/auth/login-phone", json={"phone": "13800138000", "code": "123456"}
        )

    assert response.json()["data"]["user"]["role"] == "user"


def test_role_mismatch_rejects_existing_token(monkeypatch, tmp_path):
    with _client(monkeypatch, tmp_path, "13800138000") as client:
        login = client.post(
            "/api/auth/login-phone", json={"phone": "13800138000", "code": "123456"}
        ).json()["data"]
        with sqlite3.connect(client.app.state.settings.database_path) as connection:
            connection.execute("UPDATE users SET role = 'user' WHERE user_id = ?", (login["user"]["user_id"],))

        response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {login['token']}"})

    assert response.status_code == 401


def test_standard_user_is_denied_by_operator_dependency(monkeypatch, tmp_path):
    from app.services import auth as auth_module

    assert hasattr(auth_module, "require_operator"), "require_operator must be available to operator routes"
    with _client(monkeypatch, tmp_path) as client:
        app = client.app

        @app.get("/test/operator", dependencies=[Depends(auth_module.require_operator)])
        def operator_only():
            return {"ok": True}

        login = client.post(
            "/api/auth/login-phone", json={"phone": "13900139000", "code": "123456"}
        ).json()["data"]
        response = client.get("/test/operator", headers={"Authorization": f"Bearer {login['token']}"})

    assert response.status_code == 403


def test_existing_user_id_authentication_interface_stays_compatible(api_client):
    token = api_client.headers["Authorization"].split(" ", 1)[1]

    user_id = api_client.app.state.auth_service.verify(token)

    assert isinstance(user_id, str)
    assert user_id


def test_phase10_migration_head_and_legacy_sqlite_upgrade(monkeypatch, tmp_path):
    fresh_path = tmp_path / "fresh.db"
    _upgrade(f"sqlite:///{fresh_path.as_posix()}")
    with sqlite3.connect(fresh_path) as connection:
        fresh_columns = {row[1] for row in connection.execute("PRAGMA table_info(users)")}
        fresh_annual_insight_columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info(annual_employment_insight)")
        }
        fresh_tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        fresh_revision = connection.execute("SELECT version_num FROM alembic_version").fetchone()[0]

    legacy_path = tmp_path / "legacy.db"
    _upgrade(f"sqlite:///{legacy_path.as_posix()}", "20260819_phase9")
    initialize_database(legacy_path)
    with sqlite3.connect(legacy_path) as connection:
        legacy_columns = {row[1] for row in connection.execute("PRAGMA table_info(users)")}
        legacy_annual_insight_columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info(annual_employment_insight)")
        }
    _upgrade(f"sqlite:///{legacy_path.as_posix()}")

    monkeypatch.delenv("OPERATOR_PHONE_ALLOWLIST", raising=False)
    settings = load_settings()
    assert settings.operator_phone_allowlist == ()
    assert settings.push_dispatcher_mode == "mock"
    assert settings.log_level == "INFO"
    assert settings.resume_import_max_file_bytes == 10 * 1024 * 1024
    assert settings.password_bcrypt_rounds == 12
    assert {"role"} <= fresh_columns
    assert {"role_name"} <= fresh_annual_insight_columns
    assert {"push_send_log", "resume_import", "knowledge_item", "knowledge_item_version", "background_task_run", "password_account"} <= fresh_tables
    assert fresh_revision == "20260821_phase12"
    assert {"role"} <= legacy_columns
    assert {"role_name"} <= legacy_annual_insight_columns


def test_phase10_migration_renders_postgresql_offline_sql():
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", "postgresql+psycopg://resume:secret@db.example/resume")
    output = StringIO()
    config.output_buffer = output

    command.upgrade(config, "head", sql=True)

    rendered = output.getvalue()
    assert "ALTER TABLE users ADD COLUMN role" in rendered
    assert "CREATE TABLE IF NOT EXISTS push_send_log" in rendered
