from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

from app.config import load_settings
from app.db import connect, initialize_database
from app.repositories.job_collections import JobCollectionRepository
from app.repositories.membership import MembershipRepository
from app.services.worker import BackgroundWorker, TaskLeaseRepository


def _settings(monkeypatch, database_path, temp_path):
    monkeypatch.setenv("DATABASE_PATH", str(database_path))
    monkeypatch.setenv("TEMP_FILE_PATH", str(temp_path))
    monkeypatch.setenv("EXPORT_FILE_EXPIRE_MINUTES", "1")
    monkeypatch.setenv("ORDER_PAYMENT_EXPIRE_MINUTES", "30")
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


def test_task_lease_rejects_second_owner_until_first_lease_expires(tmp_path) -> None:
    database_path = tmp_path / "worker.db"
    initialize_database(database_path)
    leases = TaskLeaseRepository(database_path)

    assert leases.acquire("order_expiry", "first", 60) is True
    assert leases.acquire("order_expiry", "second", 60) is False

    with connect(database_path) as connection:
        connection.execute(
            "UPDATE background_task_lock SET lease_expires_at = ? WHERE task_name = ?",
            ((datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat(), "order_expiry"),
        )

    assert leases.acquire("order_expiry", "second", 60) is True


def test_worker_cycle_generates_one_alert_and_expires_pending_order(monkeypatch, tmp_path) -> None:
    database_path = tmp_path / "worker.db"
    temp_path = tmp_path / "exports"
    temp_path.mkdir()
    expired_export = temp_path / "expired-export.pdf"
    unrelated_file = temp_path / "notes.txt"
    expired_export.write_bytes(b"expired export")
    unrelated_file.write_text("keep me", encoding="utf-8")
    expired_at = (datetime.now(timezone.utc) - timedelta(minutes=2)).timestamp()
    os.utime(expired_export, (expired_at, expired_at))
    os.utime(unrelated_file, (expired_at, expired_at))
    initialize_database(database_path)
    _create_user(database_path, "worker-user")
    JobCollectionRepository(database_path).set_subscription(
        "worker-user", True, "数据工程师"
    )
    order = MembershipRepository(database_path).create_order(
        "worker-user", "monthly", 1_900, False
    )
    with connect(database_path) as connection:
        connection.execute(
            "UPDATE order_record SET create_time = ? WHERE order_id = ?",
            ((datetime.now(timezone.utc) - timedelta(minutes=31)).isoformat(), order.order_id),
        )

    worker = BackgroundWorker.from_settings(
        _settings(monkeypatch, database_path, temp_path), owner_id="test-worker"
    )
    first_result = worker.run_all_once()
    second_result = worker.run_all_once()

    assert first_result["job_match_alerts"] == 1
    assert first_result["expired_exports"] == 1
    assert first_result["expired_orders"] == 1
    assert second_result["job_match_alerts"] == 0
    with connect(database_path) as connection:
        alert_count = connection.execute("SELECT COUNT(*) FROM job_match_alert").fetchone()[0]
        payment_status = connection.execute(
            "SELECT payment_status FROM order_record WHERE order_id = ?", (order.order_id,)
        ).fetchone()[0]
    assert alert_count == 1
    assert payment_status == "expired"
    assert not expired_export.exists()
    assert unrelated_file.exists()
