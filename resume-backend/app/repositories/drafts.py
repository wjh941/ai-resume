from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from uuid import uuid4

from app.db import connect
from app.schemas.draft import DraftSaveRequest


class DraftNotFoundError(Exception):
    pass


class DraftRepository:
    def __init__(self, database_path: Path):
        self.database_path = database_path

    def save(self, draft: DraftSaveRequest) -> dict:
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
                    WHERE id = ? AND client_id = ?
                    """,
                    (draft.job_title, draft.template_id, payload, now, draft_id, draft.client_id),
                )
                if cursor.rowcount == 0:
                    raise DraftNotFoundError
            else:
                connection.execute(
                    """
                    INSERT INTO user_draft
                    (id, client_id, job_title, template_id, payload_json, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (draft_id, draft.client_id, draft.job_title, draft.template_id, payload, now, now),
                )
        return self.get(draft_id, draft.client_id)

    def get(self, draft_id: str, client_id: str) -> dict:
        with connect(self.database_path) as connection:
            row = connection.execute(
                "SELECT * FROM user_draft WHERE id = ? AND client_id = ?", (draft_id, client_id)
            ).fetchone()
        if row is None:
            raise DraftNotFoundError
        return self._to_draft(row)

    def list(self, client_id: str) -> list[dict]:
        with connect(self.database_path) as connection:
            rows = connection.execute(
                "SELECT * FROM user_draft WHERE client_id = ? ORDER BY updated_at DESC, id DESC", (client_id,)
            ).fetchall()
        return [self._to_draft(row) for row in rows]

    def copy(self, draft_id: str, client_id: str) -> dict:
        source = self.get(draft_id, client_id)
        return self.save(
            DraftSaveRequest(
                client_id=client_id,
                job_title=source["job_title"],
                template_id=source["template_id"],
                resume=source["resume"],
                job_intelligence=source["job_intelligence"],
            )
        )

    def delete(self, draft_id: str, client_id: str) -> None:
        with connect(self.database_path) as connection:
            cursor = connection.execute(
                "DELETE FROM user_draft WHERE id = ? AND client_id = ?", (draft_id, client_id)
            )
        if cursor.rowcount == 0:
            raise DraftNotFoundError

    @staticmethod
    def _to_draft(row) -> dict:
        snapshot = json.loads(row["payload_json"])
        return {
            "id": row["id"],
            "client_id": row["client_id"],
            "job_title": row["job_title"],
            "template_id": row["template_id"],
            "resume": snapshot["resume"],
            "job_intelligence": snapshot["job_intelligence"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
