from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.config import load_settings
from app.db import connect, initialize_database
from app.repositories.applications import ApplicationRepository
from app.repositories.job_collections import JobCollectionRepository
from app.repositories.membership import MembershipRepository
from app.repositories.push_logs import PushLogRepository
from app.schemas.application import ApplicationSaveRequest, InterviewReminderRequest
from app.services.push import PushDispatcher
from app.services.worker import BackgroundWorker


def _settings(monkeypatch, database_path, temp_path, mode: str = "mock"):
    monkeypatch.setenv("DATABASE_PATH", str(database_path))
    monkeypatch.setenv("TEMP_FILE_PATH", str(temp_path))
    monkeypatch.setenv("PUSH_DISPATCHER_MODE", mode)
    return load_settings()


def _create_user(database_path, user_id: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with connect(database_path) as connection:
        connection.execute(
            """
            INSERT INTO users (user_id, phone, token_version, created_at, last_login)
            VALUES (?, ?, 1, ?, ?)
            """,
            (user_id, f"phone-{user_id}", now, now),
        )


def test_mock_dispatch_logs_both_targets_once(monkeypatch, tmp_path) -> None:
    database_path = tmp_path / "push.db"
    initialize_database(database_path)
    _create_user(database_path, "user-1")
    settings = _settings(monkeypatch, database_path, tmp_path / "temp")

    dispatcher = PushDispatcher(settings, PushLogRepository(database_path))
    logs = dispatcher.dispatch(
        "job_subscription_alert", "user-1", "alert-1", {"alert_id": "alert-1"}
    )

    assert {item.target_type for item in logs} == {"sms", "wechat_subscription"}
    assert {item.status for item in logs} == {"sent"}
    assert dispatcher.dispatch("job_subscription_alert", "user-1", "alert-1", {}) == []
    assert PushLogRepository(database_path).count() == 2


def test_real_dispatch_skips_both_targets_without_duplicates(monkeypatch, tmp_path) -> None:
    database_path = tmp_path / "push.db"
    initialize_database(database_path)
    _create_user(database_path, "user-1")
    settings = _settings(monkeypatch, database_path, tmp_path / "temp", "real")

    dispatcher = PushDispatcher(settings, PushLogRepository(database_path))
    logs = dispatcher.dispatch("order_change", "user-1", "order-1", {"order_id": "order-1"})

    assert {item.target_type for item in logs} == {"sms", "wechat_subscription"}
    assert {item.status for item in logs} == {"skipped"}
    assert dispatcher.dispatch("order_change", "user-1", "order-1", {}) == []
    assert PushLogRepository(database_path).count() == 2


def test_invalid_dispatcher_mode_defaults_to_mock(monkeypatch, tmp_path) -> None:
    settings = _settings(monkeypatch, tmp_path / "push.db", tmp_path / "temp", "unsupported")

    assert settings.push_dispatcher_mode == "mock"


def test_worker_dispatches_each_source_once_and_marks_mock_reminder_delivered(monkeypatch, tmp_path) -> None:
    database_path = tmp_path / "worker.db"
    temp_path = tmp_path / "temp"
    temp_path.mkdir()
    initialize_database(database_path)
    _create_user(database_path, "worker-user")
    settings = _settings(monkeypatch, database_path, temp_path)
    JobCollectionRepository(database_path).set_subscription("worker-user", True, "data engineer")
    applications = ApplicationRepository(database_path)
    application = applications.save(
        "worker-user",
        ApplicationSaveRequest(
            company="Example", role_name="Engineer", city="Beijing", source="manual", status="applied"
        ),
    )
    reminder = applications.save_reminder(
        "worker-user",
        application.id,
        InterviewReminderRequest(reminder_at=datetime.now(timezone.utc) - timedelta(minutes=1)),
    )
    order = MembershipRepository(database_path).create_order("worker-user", "monthly", 1_900, False)
    with connect(database_path) as connection:
        connection.execute(
            "UPDATE order_record SET create_time = ? WHERE order_id = ?",
            ((datetime.now(timezone.utc) - timedelta(minutes=31)).isoformat(), order.order_id),
        )

    worker = BackgroundWorker.from_settings(settings, owner_id="push-worker")
    first = worker.run_all_once()
    second = worker.run_all_once()

    assert first["push_job_alerts"] == 2
    assert first["push_interview_reminders"] == 2
    assert first["push_order_changes"] == 2
    assert second["push_job_alerts"] == 0
    assert second["push_interview_reminders"] == 0
    assert second["push_order_changes"] == 0
    with connect(database_path) as connection:
        status = connection.execute(
            "SELECT status FROM interview_reminder WHERE id = ?", (reminder["id"],)
        ).fetchone()[0]
    assert status == "delivered"
