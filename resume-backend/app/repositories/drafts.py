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
