from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.db import connect
from app.schemas.application import ApplicationRecord, ApplicationSaveRequest, ApplicationStatus


class ApplicationNotFoundError(Exception):
    pass


class ApplicationRepository:
    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path

    def list(
        self,
        user_id: str,
        status: ApplicationStatus | None = None,
    ) -> list[ApplicationRecord]:
        query = """
            SELECT * FROM application_tracker
            WHERE user_id = ?
        """
        values: list[object] = [user_id]
        if status:
            query += " AND status = ?"
            values.append(status)
        query += """
            ORDER BY
                CASE WHEN next_action_at IS NULL THEN 1 ELSE 0 END,
                next_action_at ASC,
                updated_at DESC,
                id DESC
        """
        with connect(self._database_path) as connection:
            rows = connection.execute(query, values).fetchall()
        return [self._from_row(row) for row in rows]

    def save(self, user_id: str, payload: ApplicationSaveRequest) -> ApplicationRecord:
        application_id = payload.id or str(uuid4())
        now = datetime.now(timezone.utc).isoformat()
        values = (
            payload.company,
            payload.role_name,
            payload.city,
            payload.source,
            payload.status,
            payload.applied_at.isoformat() if payload.applied_at else None,
            payload.next_action_at.isoformat() if payload.next_action_at else None,
            payload.interview_notes,
            payload.draft_id,
            payload.notes,
        )
        with connect(self._database_path) as connection:
            if payload.id:
                cursor = connection.execute(
                    """
                    UPDATE application_tracker
                    SET company = ?, role_name = ?, city = ?, source = ?, status = ?,
                        applied_at = ?, next_action_at = ?, interview_notes = ?,
                        draft_id = ?, notes = ?, updated_at = ?
                    WHERE id = ? AND user_id = ?
                    """,
                    (*values, now, application_id, user_id),
                )
                if cursor.rowcount == 0:
                    raise ApplicationNotFoundError
            else:
                connection.execute(
                    """
                    INSERT INTO application_tracker (
                        id, client_id, user_id, company, role_name, city, source, status,
                        applied_at, next_action_at, interview_notes, draft_id, notes,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (application_id, user_id, user_id, *values, now, now),
                )
            row = connection.execute(
                "SELECT * FROM application_tracker WHERE id = ? AND user_id = ?",
                (application_id, user_id),
            ).fetchone()
        if row is None:
            raise ApplicationNotFoundError
        return self._from_row(row)

    def delete(self, user_id: str, application_id: str) -> None:
        with connect(self._database_path) as connection:
            cursor = connection.execute(
                "DELETE FROM application_tracker WHERE id = ? AND user_id = ?",
                (application_id, user_id),
            )
        if cursor.rowcount == 0:
            raise ApplicationNotFoundError

    @staticmethod
    def _from_row(row) -> ApplicationRecord:
        return ApplicationRecord(
            id=str(row["id"]),
            company=str(row["company"]),
            role_name=str(row["role_name"]),
            city=str(row["city"]),
            source=str(row["source"]),
            status=str(row["status"]),
            applied_at=row["applied_at"],
            next_action_at=row["next_action_at"],
            interview_notes=str(row["interview_notes"]),
            draft_id=row["draft_id"],
            notes=str(row["notes"]),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )
