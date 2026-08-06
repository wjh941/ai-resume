from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

from app.db import connect
from app.schemas.job import JobIntelligence


def normalize_role_name(role_name: str) -> str:
    return " ".join(role_name.split()).casefold()


class JobCache:
    def __init__(self, database_path: Path, expire_days: int) -> None:
        self._database_path = database_path
        self._expire_days = expire_days

    def get(self, role_name: str, provider_mode: str) -> JobIntelligence | None:
        normalized_role = normalize_role_name(role_name)
        with connect(self._database_path) as connection:
            row = connection.execute(
                """
                SELECT payload_json, expires_at
                FROM job_cache
                WHERE normalized_role = ? AND provider_mode = ?
                """,
                (normalized_role, provider_mode),
            ).fetchone()

        if row is None or datetime.fromisoformat(row["expires_at"]) <= datetime.now(timezone.utc):
            return None
        return JobIntelligence.model_validate(json.loads(row["payload_json"]))

    def put(self, role_name: str, provider_mode: str, job: JobIntelligence) -> None:
        now = datetime.now(timezone.utc)
        normalized_role = normalize_role_name(role_name)
        with connect(self._database_path) as connection:
            connection.execute(
                """
                INSERT INTO job_cache (
                    normalized_role, provider_mode, payload_json, expires_at, created_at
                )
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(normalized_role, provider_mode) DO UPDATE SET
                    payload_json = excluded.payload_json,
                    expires_at = excluded.expires_at,
                    created_at = excluded.created_at
                """,
                (
                    normalized_role,
                    provider_mode,
                    json.dumps(job.model_dump(), ensure_ascii=False),
                    (now + timedelta(days=self._expire_days)).isoformat(),
                    now.isoformat(),
                ),
            )
