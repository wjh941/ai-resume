from __future__ import annotations

from datetime import date, datetime, timezone
import json
from pathlib import Path
from uuid import uuid4

from app.db import connect
from app.schemas.application import (
    ApplicationRecord,
    ApplicationSaveRequest,
    ApplicationStatus,
    InterviewReminderRequest,
    TimelineEvent,
    TimelineEventRequest,
)


class ApplicationNotFoundError(Exception):
    pass


class ApplicationRepository:
    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path

    def list(
        self,
        user_id: str,
        status: ApplicationStatus | None = None,
        interview_date: date | None = None,
    ) -> list[ApplicationRecord]:
        query = """
            SELECT * FROM application_tracker
            WHERE user_id = ?
        """
        values: list[object] = [user_id]
        if status:
            query += " AND status = ?"
            values.append(status)
        if interview_date:
            query += " AND substr(next_interview_at, 1, 10) = ?"
            values.append(interview_date.isoformat())
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
            payload.contact_info,
            payload.attachment_ref,
            payload.next_interview_at.isoformat() if payload.next_interview_at else None,
        )
        with connect(self._database_path) as connection:
            if payload.id:
                cursor = connection.execute(
                    """
                    UPDATE application_tracker
                    SET company = ?, role_name = ?, city = ?, source = ?, status = ?,
                        applied_at = ?, next_action_at = ?, interview_notes = ?,
                        draft_id = ?, notes = ?, contact_info = ?, attachment_ref = ?,
                        next_interview_at = ?, updated_at = ?
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
                        contact_info, attachment_ref, next_interview_at, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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

    def list_timeline(self, user_id: str, application_id: str) -> list[TimelineEvent]:
        with connect(self._database_path) as connection:
            row = self._owned_row(connection, user_id, application_id)
        return self._timeline_from_row(row)

    def add_timeline_event(
        self,
        user_id: str,
        application_id: str,
        payload: TimelineEventRequest,
    ) -> TimelineEvent:
        event = TimelineEvent(id=str(uuid4()), **payload.model_dump())
        with connect(self._database_path) as connection:
            row = self._owned_row(connection, user_id, application_id)
            timeline = self._timeline_from_row(row)
            timeline.append(event)
            connection.execute(
                """
                UPDATE application_tracker
                SET timeline_json = ?, updated_at = ?
                WHERE id = ? AND user_id = ?
                """,
                (
                    json.dumps([item.model_dump(mode="json") for item in timeline], ensure_ascii=False),
                    datetime.now(timezone.utc).isoformat(),
                    application_id,
                    user_id,
                ),
            )
        return event

    def save_reminder(
        self,
        user_id: str,
        application_id: str,
        payload: InterviewReminderRequest,
    ) -> dict[str, str]:
        reminder_id = str(uuid4())
        now = datetime.now(timezone.utc).isoformat()
        with connect(self._database_path) as connection:
            self._owned_row(connection, user_id, application_id)
            connection.execute(
                """
                INSERT INTO interview_reminder
                (id, user_id, application_id, reminder_at, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, 'pending', ?, ?)
                """,
                (reminder_id, user_id, application_id, payload.reminder_at.isoformat(), now, now),
            )
        return {
            "id": reminder_id,
            "application_id": application_id,
            "reminder_at": payload.reminder_at.isoformat(),
            "status": "pending",
        }

    def delete(self, user_id: str, application_id: str) -> None:
        with connect(self._database_path) as connection:
            cursor = connection.execute(
                "DELETE FROM application_tracker WHERE id = ? AND user_id = ?",
                (application_id, user_id),
            )
        if cursor.rowcount == 0:
            raise ApplicationNotFoundError

    @staticmethod
    def _owned_row(connection, user_id: str, application_id: str):
        row = connection.execute(
            "SELECT * FROM application_tracker WHERE id = ? AND user_id = ?",
            (application_id, user_id),
        ).fetchone()
        if row is None:
            raise ApplicationNotFoundError
        return row

    @staticmethod
    def _timeline_from_row(row) -> list[TimelineEvent]:
        try:
            raw_timeline = json.loads(str(row["timeline_json"] or "[]"))
        except (TypeError, json.JSONDecodeError):
            return []
        if not isinstance(raw_timeline, list):
            return []
        events: list[TimelineEvent] = []
        for item in raw_timeline:
            if not isinstance(item, dict):
                continue
            try:
                events.append(TimelineEvent.model_validate(item))
            except ValueError:
                continue
        return events

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
            contact_info=str(row["contact_info"] or ""),
            attachment_ref=str(row["attachment_ref"] or ""),
            next_interview_at=row["next_interview_at"],
            timeline=ApplicationRepository._timeline_from_row(row),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )
