from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from uuid import uuid4

from app.db import connect
from app.schemas.draft import DraftSaveRequest


class DraftNotFoundError(Exception):
    pass


class DraftLimitReachedError(Exception):
    pass


class DraftRepository:
    def __init__(self, database_path: Path):
        self.database_path = database_path

    def save(
        self,
        user_id: str,
        draft: DraftSaveRequest,
        max_drafts: int | None = None,
    ) -> dict:
        draft_id = draft.id or str(uuid4())
        now = datetime.now(timezone.utc).isoformat()
        payload = json.dumps(
            {
                "version": 1,
                "resume": draft.resume.model_dump(mode="json"),
                "job_intelligence": (
                    draft.job_intelligence.model_dump(mode="json") if draft.job_intelligence else None
                ),
            }
        )
        with connect(self.database_path) as connection:
            if draft.id:
                cursor = connection.execute(
                    """
                    UPDATE user_draft
                    SET job_title = ?, template_id = ?, payload_json = ?, updated_at = ?
                    WHERE id = ? AND user_id = ?
                    """,
                    (draft.job_title, draft.template_id, payload, now, draft_id, user_id),
                )
                if cursor.rowcount == 0:
                    raise DraftNotFoundError
            else:
                if max_drafts is not None:
                    # 额度检查和新增必须位于同一个写事务，避免两个并发请求越过免费版上限。
                    connection.execute("BEGIN IMMEDIATE")
                    count = connection.execute(
                        "SELECT COUNT(*) FROM user_draft WHERE user_id = ?", (user_id,)
                    ).fetchone()[0]
                    if count >= max_drafts:
                        raise DraftLimitReachedError
                connection.execute(
                    """
                    INSERT INTO user_draft
                    (id, client_id, user_id, job_title, template_id, payload_json, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (draft_id, user_id, user_id, draft.job_title, draft.template_id, payload, now, now),
                )
        return self.get(user_id, draft_id)

    def get(self, user_id: str, draft_id: str) -> dict:
        with connect(self.database_path) as connection:
            row = connection.execute(
                "SELECT * FROM user_draft WHERE id = ? AND user_id = ?", (draft_id, user_id)
            ).fetchone()
        if row is None:
            raise DraftNotFoundError
        return self._to_draft(row)

    def list(self, user_id: str) -> list[dict]:
        with connect(self.database_path) as connection:
            rows = connection.execute(
                "SELECT * FROM user_draft WHERE user_id = ? ORDER BY updated_at DESC, id DESC", (user_id,)
            ).fetchall()
        return [self._to_draft(row) for row in rows]

    def copy(self, user_id: str, draft_id: str, max_drafts: int | None = None) -> dict:
        source = self.get(user_id, draft_id)
        return self.save(
            user_id,
            DraftSaveRequest(
                job_title=source["job_title"],
                template_id=source["template_id"],
                resume=source["resume"],
                job_intelligence=source["job_intelligence"],
            ),
            max_drafts=max_drafts,
        )

    def delete(self, user_id: str, draft_id: str) -> None:
        with connect(self.database_path) as connection:
            cursor = connection.execute(
                "DELETE FROM user_draft WHERE id = ? AND user_id = ?", (draft_id, user_id)
            )
        if cursor.rowcount == 0:
            raise DraftNotFoundError

    def create_version(self, user_id: str, draft_id: str, note: str) -> dict:
        version_id = str(uuid4())
        now = datetime.now(timezone.utc).isoformat()
        with connect(self.database_path) as connection:
            source = connection.execute(
                "SELECT job_title, template_id, payload_json FROM user_draft WHERE id = ? AND user_id = ?",
                (draft_id, user_id),
            ).fetchone()
            if source is None:
                raise DraftNotFoundError
            snapshot = {
                "job_title": source["job_title"],
                "template_id": source["template_id"],
                "payload": json.loads(source["payload_json"]),
            }
            connection.execute(
                "UPDATE resume_version SET is_active = 0 WHERE user_id = ? AND draft_id = ?",
                (user_id, draft_id),
            )
            connection.execute(
                """
                INSERT INTO resume_version (id, user_id, draft_id, note, payload_json, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, 1, ?)
                """,
                (version_id, user_id, draft_id, note, json.dumps(snapshot, ensure_ascii=False), now),
            )
        return {"id": version_id, "note": note, "is_active": True, "created_at": now}

    def list_versions(self, user_id: str, draft_id: str) -> list[dict]:
        self.get(user_id, draft_id)
        with connect(self.database_path) as connection:
            rows = connection.execute(
                """
                SELECT id, note, is_active, created_at FROM resume_version
                WHERE user_id = ? AND draft_id = ?
                ORDER BY created_at DESC, id DESC
                """,
                (user_id, draft_id),
            ).fetchall()
        return [
            {
                "id": str(row["id"]),
                "note": str(row["note"]),
                "is_active": bool(row["is_active"]),
                "created_at": str(row["created_at"]),
            }
            for row in rows
        ]

    def restore_version(self, user_id: str, draft_id: str, version_id: str) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        with connect(self.database_path) as connection:
            version = connection.execute(
                """
                SELECT payload_json FROM resume_version
                WHERE id = ? AND user_id = ? AND draft_id = ?
                """,
                (version_id, user_id, draft_id),
            ).fetchone()
            if version is None:
                raise DraftNotFoundError
            snapshot = json.loads(version["payload_json"])
            cursor = connection.execute(
                """
                UPDATE user_draft
                SET job_title = ?, template_id = ?, payload_json = ?, updated_at = ?
                WHERE id = ? AND user_id = ?
                """,
                (
                    snapshot["job_title"],
                    snapshot["template_id"],
                    json.dumps(snapshot["payload"], ensure_ascii=False),
                    now,
                    draft_id,
                    user_id,
                ),
            )
            if cursor.rowcount == 0:
                raise DraftNotFoundError
            connection.execute(
                "UPDATE resume_version SET is_active = 0 WHERE user_id = ? AND draft_id = ?",
                (user_id, draft_id),
            )
            connection.execute("UPDATE resume_version SET is_active = 1 WHERE id = ?", (version_id,))
        return self.get(user_id, draft_id)

    def compare_versions(
        self,
        user_id: str,
        draft_id: str,
        left_id: str,
        right_id: str,
    ) -> dict:
        left = self._version_snapshot(user_id, draft_id, left_id)
        right = self._version_snapshot(user_id, draft_id, right_id)
        changed_fields = [
            field
            for field in ("job_title", "template_id", "resume", "job_intelligence")
            if self._snapshot_value(left, field) != self._snapshot_value(right, field)
        ]
        return {"left_id": left_id, "right_id": right_id, "changed_fields": changed_fields}

    def _version_snapshot(self, user_id: str, draft_id: str, version_id: str) -> dict:
        with connect(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT payload_json FROM resume_version
                WHERE id = ? AND user_id = ? AND draft_id = ?
                """,
                (version_id, user_id, draft_id),
            ).fetchone()
        if row is None:
            raise DraftNotFoundError
        return json.loads(row["payload_json"])

    @staticmethod
    def _snapshot_value(snapshot: dict, field: str):
        if field in {"job_title", "template_id"}:
            return snapshot.get(field)
        return snapshot.get("payload", {}).get(field)

    @staticmethod
    def _to_draft(row) -> dict:
        snapshot = json.loads(row["payload_json"])
        return {
            "id": row["id"],
            "job_title": row["job_title"],
            "template_id": row["template_id"],
            "resume": snapshot["resume"],
            "job_intelligence": snapshot["job_intelligence"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
