from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.db import connect
from app.schemas.job_collections import FavoriteJobCreate


class FavoriteJobNotFoundError(Exception):
    pass


@dataclass(frozen=True)
class FavoriteJobRecord:
    id: str
    role_name: str
    note: str
    created_at: str

    def as_dict(self) -> dict[str, str]:
        return {"id": self.id, "role_name": self.role_name, "note": self.note, "created_at": self.created_at}


@dataclass(frozen=True)
class JobSubscriptionRecord:
    enabled: bool
    match_filter: str
    last_notify_at: str | None

    def as_dict(self) -> dict[str, object]:
        return {
            "enabled": self.enabled,
            "match_filter": self.match_filter,
            "last_notify_at": self.last_notify_at,
        }


class JobCollectionRepository:
    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path

    def list_favorites(self, user_id: str) -> list[FavoriteJobRecord]:
        with connect(self._database_path) as connection:
            rows = connection.execute(
                "SELECT id, role_name, note, created_at FROM job_favorite WHERE user_id = ? ORDER BY created_at DESC, id DESC",
                (user_id,),
            ).fetchall()
        return [self._favorite_from_row(row) for row in rows]

    def save_favorite(self, user_id: str, payload: FavoriteJobCreate) -> FavoriteJobRecord:
        now = datetime.now(timezone.utc).isoformat()
        favorite_id = str(uuid4())
        with connect(self._database_path) as connection:
            connection.execute(
                """
                INSERT INTO job_favorite (id, user_id, role_name, note, created_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(user_id, role_name) DO UPDATE SET note = excluded.note
                """,
                (favorite_id, user_id, payload.role_name, payload.note, now),
            )
            row = connection.execute(
                "SELECT id, role_name, note, created_at FROM job_favorite WHERE user_id = ? AND role_name = ?",
                (user_id, payload.role_name),
            ).fetchone()
        if row is None:
            raise FavoriteJobNotFoundError
        return self._favorite_from_row(row)

    def delete_favorite(self, user_id: str, favorite_id: str) -> None:
        with connect(self._database_path) as connection:
            cursor = connection.execute(
                "DELETE FROM job_favorite WHERE id = ? AND user_id = ?",
                (favorite_id, user_id),
            )
        if cursor.rowcount == 0:
            raise FavoriteJobNotFoundError

    def subscription(self, user_id: str) -> JobSubscriptionRecord:
        with connect(self._database_path) as connection:
            row = connection.execute(
                "SELECT enabled, match_filter, last_notify_at FROM job_match_subscription WHERE user_id = ?",
                (user_id,),
            ).fetchone()
        if row is None:
            return JobSubscriptionRecord(False, "", None)
        return JobSubscriptionRecord(
            bool(row["enabled"]),
            str(row["match_filter"]),
            str(row["last_notify_at"]) if row["last_notify_at"] else None,
        )

    def set_subscription(self, user_id: str, enabled: bool, match_filter: str | None) -> JobSubscriptionRecord:
        now = datetime.now(timezone.utc).isoformat()
        with connect(self._database_path) as connection:
            connection.execute(
                """
                INSERT INTO job_match_subscription (user_id, enabled, match_filter, updated_at)
                VALUES (?, ?, COALESCE(?, ''), ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    enabled = excluded.enabled,
                    match_filter = CASE WHEN ? IS NULL THEN job_match_subscription.match_filter ELSE excluded.match_filter END,
                    updated_at = excluded.updated_at
                """,
                (user_id, int(enabled), match_filter, now, match_filter),
            )
        # TODO: A future notification worker sets last_notify_at after a successful alert delivery.
        return self.subscription(user_id)

    def subscription_enabled(self, user_id: str) -> bool:
        return self.subscription(user_id).enabled

    def set_subscription_enabled(self, user_id: str, enabled: bool) -> bool:
        return self.set_subscription(user_id, enabled, None).enabled

    def create_pending_alerts(self) -> int:
        now = datetime.now(timezone.utc)
        alert_date = now.date().isoformat()
        created = 0
        with connect(self._database_path) as connection:
            subscriptions = connection.execute(
                """
                SELECT user_id, match_filter, last_notify_at
                FROM job_match_subscription
                WHERE enabled = 1
                """
            ).fetchall()
            for subscription in subscriptions:
                last_notify_at = subscription["last_notify_at"]
                if last_notify_at and str(last_notify_at).startswith(alert_date):
                    continue
                alert_key = f"{subscription['user_id']}:{alert_date}"
                cursor = connection.execute(
                    """
                    INSERT OR IGNORE INTO job_match_alert
                    (id, user_id, alert_key, match_filter, status, created_at)
                    VALUES (?, ?, ?, ?, 'pending', ?)
                    """,
                    (
                        str(uuid4()),
                        subscription["user_id"],
                        alert_key,
                        subscription["match_filter"],
                        now.isoformat(),
                    ),
                )
                if cursor.rowcount:
                    connection.execute(
                        "UPDATE job_match_subscription SET last_notify_at = ? WHERE user_id = ?",
                        (now.isoformat(), subscription["user_id"]),
                    )
                    created += 1
        return created

    def create_pending_alerts(self) -> int:
        now = datetime.now(timezone.utc)
        alert_date = now.date().isoformat()
        created = 0
        with connect(self._database_path) as connection:
            subscriptions = connection.execute(
                """
                SELECT user_id, match_filter, last_notify_at
                FROM job_match_subscription
                WHERE enabled = 1
                """
            ).fetchall()
            for subscription in subscriptions:
                last_notify_at = subscription["last_notify_at"]
                if last_notify_at and str(last_notify_at).startswith(alert_date):
                    continue
                alert_key = f"{subscription['user_id']}:{alert_date}"
                cursor = connection.execute(
                    """
                    INSERT OR IGNORE INTO job_match_alert
                    (id, user_id, alert_key, match_filter, status, created_at)
                    VALUES (?, ?, ?, ?, 'pending', ?)
                    """,
                    (
                        str(uuid4()),
                        subscription["user_id"],
                        alert_key,
                        subscription["match_filter"],
                        now.isoformat(),
                    ),
                )
                if cursor.rowcount:
                    connection.execute(
                        "UPDATE job_match_subscription SET last_notify_at = ? WHERE user_id = ?",
                        (now.isoformat(), subscription["user_id"]),
                    )
                    created += 1
        return created

    @staticmethod
    def _favorite_from_row(row) -> FavoriteJobRecord:
        return FavoriteJobRecord(
            id=str(row["id"]),
            role_name=str(row["role_name"]),
            note=str(row["note"]),
            created_at=str(row["created_at"]),
        )
