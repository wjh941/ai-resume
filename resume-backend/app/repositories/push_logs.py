from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from uuid import uuid4

from app.db import DatabaseTarget, connect


@dataclass(frozen=True)
class PushSendLog:
    id: str
    event_type: str
    user_id: str
    source_ref: str
    target_type: str
    dispatcher_mode: str
    status: str
    payload_summary: str
    error_trace: str | None
    created_at: str


class PushLogRepository:
    def __init__(self, database_target: DatabaseTarget) -> None:
        self._database_target = database_target

    def exists_for_source(self, event_type: str, target_type: str, source_ref: str) -> bool:
        with connect(self._database_target) as connection:
            row = connection.execute(
                "SELECT 1 FROM push_send_log WHERE event_type = ? AND target_type = ? AND source_ref = ?",
                (event_type, target_type, source_ref),
            ).fetchone()
        return row is not None

    def create(
        self,
        event_type: str,
        user_id: str,
        source_ref: str,
        target_type: str,
        dispatcher_mode: str,
        status: str,
        payload: dict[str, object],
        error_trace: str | None = None,
    ) -> PushSendLog | None:
        log_id = str(uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        payload_summary = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)[:1000]
        with connect(self._database_target) as connection:
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO push_send_log
                (id, event_type, user_id, source_ref, target_type, dispatcher_mode, status,
                 payload_summary, error_trace, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    log_id,
                    event_type,
                    user_id,
                    source_ref,
                    target_type,
                    dispatcher_mode,
                    status,
                    payload_summary,
                    error_trace,
                    created_at,
                ),
            )
            if cursor.rowcount == 0:
                return None
        return PushSendLog(
            log_id,
            event_type,
            user_id,
            source_ref,
            target_type,
            dispatcher_mode,
            status,
            payload_summary,
            error_trace,
            created_at,
        )

    def count(self) -> int:
        with connect(self._database_target) as connection:
            return int(connection.execute("SELECT COUNT(*) FROM push_send_log").fetchone()[0])
