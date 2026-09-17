from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
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


class JobPlanCache:
    """个人化岗位规划缓存：键含 user_id，TTL 按“小时”配置（默认 24h）。

    与 JobCache（市场级、全员共享）不同，规划结果依赖账户资料，必须按账号隔离。
    """

    def __init__(self, database_path: Path, expire_hours: int = 24) -> None:
        self._database_path = database_path
        self._expire_hours = expire_hours

    @staticmethod
    def build_key(user_id: str, role_name: str, expand_detail: bool, provider_key: str) -> str:
        normalized_role = normalize_role_name(role_name)
        raw = f"{user_id}|{normalized_role}|{int(expand_detail)}|{provider_key}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get(self, cache_key: str) -> dict[str, object] | None:
        with connect(self._database_path) as connection:
            row = connection.execute(
                "SELECT payload_json, expires_at FROM job_plan_cache WHERE cache_key = ?",
                (cache_key,),
            ).fetchone()
        if row is None or datetime.fromisoformat(row["expires_at"]) <= datetime.now(timezone.utc):
            return None
        payload = json.loads(row["payload_json"])
        return payload if isinstance(payload, dict) else None

    def put(self, cache_key: str, payload: dict[str, object]) -> None:
        now = datetime.now(timezone.utc)
        with connect(self._database_path) as connection:
            connection.execute(
                """
                INSERT INTO job_plan_cache (cache_key, payload_json, expires_at, created_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(cache_key) DO UPDATE SET
                    payload_json = excluded.payload_json,
                    expires_at = excluded.expires_at,
                    created_at = excluded.created_at
                """,
                (
                    cache_key,
                    json.dumps(payload, ensure_ascii=False),
                    (now + timedelta(hours=self._expire_hours)).isoformat(),
                    now.isoformat(),
                ),
            )
