from __future__ import annotations

from io import StringIO
from pathlib import Path
import sqlite3

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient


BACKEND_ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "correct-horse-battery-staple"


def test_password_register_then_login_issues_existing_jwt(api_client):
    registered = api_client.post(
        "/api/auth/register-password",
        json={"account": "Project.Owner", "password": PASSWORD},
    )

    assert registered.status_code == 200
    registered_data = registered.json()["data"]
    assert registered_data["token"]
    assert registered_data["user"]["account"] == "project.owner"

    logged_in = api_client.post(
        "/api/auth/login-password",
        json={"account": "PROJECT.OWNER", "password": PASSWORD},
    )

    assert logged_in.status_code == 200
    assert logged_in.json()["data"]["user"]["user_id"] == registered_data["user"]["user_id"]
    assert api_client.get(
        "/api/template/list",
        headers={"Authorization": f"Bearer {logged_in.json()['data']['token']}"},
    ).status_code == 200


def test_password_account_rejects_duplicates_and_invalid_credentials(api_client):
    created = api_client.post(
        "/api/auth/register-password",
        json={"account": "owner", "password": PASSWORD},
    )
    duplicate = api_client.post(
        "/api/auth/register-password",
        json={"account": "OWNER", "password": PASSWORD},
    )
    wrong_password = api_client.post(
        "/api/auth/login-password",
        json={"account": "owner", "password": "a-different-strong-password"},
    )
    unknown_account = api_client.post(
        "/api/auth/login-password",
        json={"account": "missing", "password": PASSWORD},
    )

    assert created.status_code == 200
    assert duplicate.status_code == 409
    assert wrong_password.status_code == unknown_account.status_code == 401


def test_password_registration_does_not_store_plaintext_or_depend_on_sms(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "password-auth.db"))
    monkeypatch.setenv("TEMP_FILE_PATH", str(tmp_path / "temp"))
    monkeypatch.setenv("AUTH_DEMO_MODE", "false")
    monkeypatch.setenv("SMS_PROVIDER", "disabled")
    monkeypatch.setenv("JWT_SECRET", "password-auth-test-secret-with-more-than-32-bytes")
    from main import create_app

    with TestClient(create_app()) as client:
        response = client.post(
            "/api/auth/register-password",
            json={"account": "offline-owner", "password": PASSWORD},
        )

    assert response.status_code == 200
    with sqlite3.connect(tmp_path / "password-auth.db") as connection:
        password_hash = connection.execute(
            "SELECT password_hash FROM password_account WHERE account = ?", ("offline-owner",)
        ).fetchone()[0]
    assert password_hash.startswith("$2")
    assert PASSWORD not in password_hash


def test_password_account_migration_renders_postgresql_sql():
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", "postgresql+psycopg://resume:secret@db.example/resume")
    output = StringIO()
    config.output_buffer = output

    command.upgrade(config, "head", sql=True)

    assert "CREATE TABLE IF NOT EXISTS password_account" in output.getvalue()
