from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from app.config import Settings
from app.db import DatabaseTarget, connect
from app.repositories.applications import ApplicationRepository
from app.repositories.job_collections import JobCollectionRepository
from app.repositories.membership import MembershipRepository
from app.repositories.push_logs import PushLogRepository
from app.services.downloads import DownloadService
from app.services.push import PushDispatcher


class TaskLeaseRepository:
    def __init__(self, database_target: DatabaseTarget) -> None:
        self._database_target = database_target

    def acquire(self, task_name: str, owner_id: str, ttl_seconds: int) -> bool:
        now = datetime.now(timezone.utc)
        expires_at = (now + timedelta(seconds=max(1, ttl_seconds))).isoformat()
        with connect(self._database_target) as connection:
            created = connection.execute(
                """
                INSERT OR IGNORE INTO background_task_lock
                (task_name, owner_id, lease_expires_at, updated_at)
                VALUES (?, ?, ?, ?)
                """,
                (task_name, owner_id, expires_at, now.isoformat()),
            )
            if created.rowcount == 1:
                return True
            renewed = connection.execute(
                """
                UPDATE background_task_lock
                SET owner_id = ?, lease_expires_at = ?, updated_at = ?
                WHERE task_name = ? AND lease_expires_at <= ?
                """,
                (owner_id, expires_at, now.isoformat(), task_name, now.isoformat()),
            )
        return renewed.rowcount == 1

    def release(self, task_name: str, owner_id: str) -> None:
        with connect(self._database_target) as connection:
            connection.execute(
                "DELETE FROM background_task_lock WHERE task_name = ? AND owner_id = ?",
                (task_name, owner_id),
            )


class TaskRunRepository:
    def __init__(self, database_target: DatabaseTarget) -> None:
        self._database_target = database_target

    def record(self, task_name: str, processed_count: int) -> None:
        with connect(self._database_target) as connection:
            connection.execute(
                """
                INSERT INTO background_task_run (task_name, status, processed_count, completed_at)
                VALUES (?, 'completed', ?, ?)
                ON CONFLICT(task_name) DO UPDATE SET
                    status = excluded.status,
                    processed_count = excluded.processed_count,
                    completed_at = excluded.completed_at
                """,
                (task_name, processed_count, datetime.now(timezone.utc).isoformat()),
            )


class BackgroundWorker:
    def __init__(
        self,
        settings: Settings,
        database_target: DatabaseTarget,
        temp_directory: Path,
        export_expire_minutes: int,
        order_expire_minutes: int,
        lock_ttl_seconds: int,
        owner_id: str | None = None,
    ) -> None:
        self._leases = TaskLeaseRepository(database_target)
        self._runs = TaskRunRepository(database_target)
        self._jobs = JobCollectionRepository(database_target)
        self._applications = ApplicationRepository(database_target)
        self._membership = MembershipRepository(database_target)
        self._push = PushDispatcher(settings, PushLogRepository(database_target))
        self._downloads = DownloadService(database_target, temp_directory, export_expire_minutes)
        self._order_expire_minutes = order_expire_minutes
        self._lock_ttl_seconds = lock_ttl_seconds
        self._owner_id = owner_id or uuid4().hex

    @classmethod
    def from_settings(cls, settings: Settings, owner_id: str | None = None) -> "BackgroundWorker":
        return cls(
            settings,
            settings.database_target,
            settings.temp_file_path,
            settings.export_file_expire_minutes,
            settings.order_payment_expire_minutes,
            settings.worker_lock_ttl_seconds,
            owner_id,
        )

    def run_all_once(self) -> dict[str, int]:
        return {
            "job_match_alerts": self._run_with_lease(
                "job_match_alerts", self._jobs.create_pending_alerts
            ),
            "expired_exports": self._run_with_lease(
                "expired_exports", self._downloads.cleanup_expired
            ),
            "expired_orders": self._run_with_lease(
                "expired_orders",
                lambda: self._membership.expire_all_pending_orders(
                    self._order_expire_minutes
                ),
            ),
            "push_job_alerts": self._run_with_lease(
                "push_job_alerts", self._push_job_alerts
            ),
            "push_interview_reminders": self._run_with_lease(
                "push_interview_reminders", self._push_interview_reminders
            ),
            "push_order_changes": self._run_with_lease(
                "push_order_changes", self._push_order_changes
            ),
        }

    def _push_job_alerts(self) -> int:
        return sum(
            len(
                self._push.dispatch(
                    "job_subscription_alert",
                    alert["user_id"],
                    alert["id"],
                    {"alert_id": alert["id"], "match_filter": alert["match_filter"]},
                )
            )
            for alert in self._jobs.list_pending_alerts()
        )

    def _push_interview_reminders(self) -> int:
        delivered = 0
        for reminder in self._applications.list_due_pending_reminders():
            logs = self._push.dispatch(
                "interview_reminder",
                reminder["user_id"],
                reminder["id"],
                {"application_id": reminder["application_id"], "reminder_at": reminder["reminder_at"]},
            )
            delivered += len(logs)
            if logs and self._push.mode == "mock":
                self._applications.mark_reminder_delivered(reminder["id"])
        return delivered

    def _push_order_changes(self) -> int:
        return sum(
            len(
                self._push.dispatch(
                    "order_change",
                    order["user_id"],
                    order["order_id"],
                    {"order_id": order["order_id"], "package_type": order["package_type"]},
                )
            )
            for order in self._membership.list_expired_orders()
        )

    def _run_with_lease(self, task_name: str, operation) -> int:
        if not self._leases.acquire(task_name, self._owner_id, self._lock_ttl_seconds):
            return 0
        try:
            processed_count = int(operation())
            self._runs.record(task_name, processed_count)
            return processed_count
        finally:
            self._leases.release(task_name, self._owner_id)
