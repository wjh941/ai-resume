from __future__ import annotations

import sqlite3
import sys

from fastapi.testclient import TestClient


def test_psycopg_errors_map_to_sanitized_database_error_envelope(api_client):
    from psycopg import Error as PsycopgError

    @api_client.app.get("/test-psycopg-error")
    def raise_psycopg_error():
        raise PsycopgError("relation detail that must stay server-side")

    with TestClient(api_client.app, raise_server_exceptions=False) as client:
        response = client.get("/test-psycopg-error")

    assert response.status_code == 503
    assert response.json()["code"] == "database_error"
    assert "relation detail" not in response.text


def test_psycopg_handler_is_registered_when_dependency_available(api_client):
    from psycopg import Error as PsycopgError

    assert PsycopgError in api_client.app.exception_handlers
    assert sqlite3.Error in api_client.app.exception_handlers


def test_create_app_skips_psycopg_handler_when_dependency_missing(monkeypatch, tmp_path):
    from psycopg import Error as PsycopgError

    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "no-psycopg.db"))
    monkeypatch.setenv("TEMP_FILE_PATH", str(tmp_path / "temp"))
    monkeypatch.setenv("AUTH_DEMO_MODE", "true")
    monkeypatch.setenv("JWT_SECRET", "test-jwt-secret-for-authentication")
    # sys.modules 中置 None 会让 `from psycopg import Error` 抛出 ImportError，
    # 模拟纯 SQLite 部署未安装可选依赖 psycopg 的场景。
    monkeypatch.setitem(sys.modules, "psycopg", None)

    from main import create_app

    app = create_app()

    assert sqlite3.Error in app.exception_handlers
    assert PsycopgError not in app.exception_handlers
