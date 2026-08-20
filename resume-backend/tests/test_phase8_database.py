from __future__ import annotations

import sqlite3
from pathlib import Path

from alembic import command
from alembic.config import Config

from app.config import load_settings
from app.db import PostgresConnection


BACKEND_ROOT = Path(__file__).resolve().parents[1]


def _upgrade(url: str) -> None:
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", url)
    command.upgrade(config, "head")


def test_database_url_selects_postgresql_without_changing_sqlite_path(monkeypatch, tmp_path):
    sqlite_path = tmp_path / "resume.db"
    url = "postgresql+psycopg://resume:secret@db.example/resume"
    monkeypatch.setenv("DATABASE_PATH", str(sqlite_path))
    monkeypatch.setenv("DATABASE_URL", url)

    settings = load_settings()

    assert settings.database_kind == "postgresql"
    assert settings.database_target == url
    assert settings.database_path == sqlite_path.resolve()


def test_alembic_creates_current_schema_on_fresh_sqlite_database(tmp_path):
    database_path = tmp_path / "current.db"

    _upgrade(f"sqlite:///{database_path.as_posix()}")

    with sqlite3.connect(database_path) as connection:
        users = {row[1] for row in connection.execute("PRAGMA table_info(users)")}
        subscriptions = {row[1] for row in connection.execute("PRAGMA table_info(job_match_subscription)")}
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        revision = connection.execute("SELECT version_num FROM alembic_version").fetchone()[0]

    assert {"is_deleted", "deleted_at", "privacy_consent_at"} <= users
    assert {"match_filter", "last_notify_at"} <= subscriptions
    assert {"background_task_lock", "career_task", "interview_reminder", "resume_version", "password_account"} <= tables
    assert revision == "20260821_phase11"


def test_postgres_connection_translates_existing_sqlite_insert_idioms():
    received: list[tuple[str, tuple[str, ...]]] = []

    class CaptureConnection:
        def execute(self, statement, parameters=()):
            received.append((statement, tuple(parameters)))
            return "cursor"

    connection = PostgresConnection(CaptureConnection())

    result = connection.execute(
        "INSERT OR IGNORE INTO template_table (id, created_at) VALUES (?, datetime('now'))",
        ("technology",),
    )

    assert result == "cursor"
    assert received == [
        (
            "INSERT INTO template_table (id, created_at) VALUES (%s, CURRENT_TIMESTAMP) ON CONFLICT DO NOTHING",
            ("technology",),
        )
    ]
