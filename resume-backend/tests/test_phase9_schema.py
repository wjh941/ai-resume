from __future__ import annotations

from app.config import load_settings
from app.db import connect, initialize_database


def test_phase9_sqlite_schema_adds_fields_without_replacing_application_table(tmp_path) -> None:
    database_path = tmp_path / "phase9.db"

    initialize_database(database_path)

    with connect(database_path) as connection:
        columns = {
            str(row["name"])
            for row in connection.execute("PRAGMA table_info(application_tracker)")
        }
        tables = {
            str(row["name"])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }

    assert {"contact_info", "attachment_ref", "timeline_json", "next_interview_at"} <= columns
    assert {
        "background_task_lock",
        "job_match_alert",
        "interview_reminder",
        "resume_version",
        "career_task",
    } <= tables


def test_settings_read_worker_configuration(monkeypatch) -> None:
    monkeypatch.setenv("WORKER_ENABLED", "true")
    monkeypatch.setenv("TASK_SCAN_INTERVAL_SECONDS", "45")
    monkeypatch.setenv("WORKER_LOCK_TTL_SECONDS", "90")

    settings = load_settings()

    assert getattr(settings, "worker_enabled", None) is True
    assert getattr(settings, "worker_scan_interval_seconds", None) == 45
    assert getattr(settings, "worker_lock_ttl_seconds", None) == 90
