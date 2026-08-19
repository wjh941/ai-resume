from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.db import connect
from app.schemas.career import CareerTaskRecord, CareerTaskSaveRequest, CareerTaskUpdateRequest, ComparisonActionPlan


class CareerTaskNotFoundError(Exception):
    pass


class CareerTaskRepository:
    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path

    def list(self, user_id: str, plan_id: str) -> list[CareerTaskRecord]:
        with connect(self._database_path) as connection:
            rows = connection.execute(
                """
                SELECT * FROM career_task
                WHERE user_id = ? AND plan_id = ?
                ORDER BY CASE WHEN status = 'completed' THEN 1 ELSE 0 END, due_date ASC, updated_at DESC, id DESC
                """,
                (user_id, plan_id),
            ).fetchall()
        return [self._from_row(row) for row in rows]

    def save(self, user_id: str, payload: CareerTaskSaveRequest) -> CareerTaskRecord:
        task_id = payload.id or str(uuid4())
        now = datetime.now(timezone.utc).isoformat()
        values = (
            payload.plan_id,
            payload.title,
            payload.description,
            payload.due_date.isoformat() if payload.due_date else None,
            payload.status,
            payload.link_to_application_id,
            payload.link_to_evidence_id,
        )
        with connect(self._database_path) as connection:
            if payload.id:
                cursor = connection.execute(
                    """
                    UPDATE career_task
                    SET plan_id = ?, title = ?, description = ?, due_date = ?, status = ?,
                        link_to_application_id = ?, link_to_evidence_id = ?, updated_at = ?
                    WHERE id = ? AND user_id = ?
                    """,
                    (*values, now, task_id, user_id),
                )
                if cursor.rowcount == 0:
                    raise CareerTaskNotFoundError
            else:
                connection.execute(
                    """
                    INSERT INTO career_task
                    (id, user_id, plan_id, title, description, due_date, status,
                     link_to_application_id, link_to_evidence_id, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (task_id, user_id, *values, now, now),
                )
            row = connection.execute(
                "SELECT * FROM career_task WHERE id = ? AND user_id = ?", (task_id, user_id)
            ).fetchone()
        if row is None:
            raise CareerTaskNotFoundError
        return self._from_row(row)

    def update(self, user_id: str, task_id: str, payload: CareerTaskUpdateRequest) -> CareerTaskRecord:
        current = self.get(user_id, task_id)
        values = current.model_dump()
        values.update(payload.model_dump(exclude_unset=True))
        values["id"] = task_id
        return self.save(user_id, CareerTaskSaveRequest.model_validate(values))

    def delete(self, user_id: str, task_id: str) -> None:
        with connect(self._database_path) as connection:
            cursor = connection.execute(
                "DELETE FROM career_task WHERE id = ? AND user_id = ?", (task_id, user_id)
            )
        if cursor.rowcount == 0:
            raise CareerTaskNotFoundError

    def generate_from_action_plan(
        self,
        user_id: str,
        plan_id: str,
        action_plan: ComparisonActionPlan,
    ) -> list[CareerTaskRecord]:
        created: list[CareerTaskRecord] = []
        with connect(self._database_path) as connection:
            rows = connection.execute(
                """
                SELECT title FROM career_task
                WHERE user_id = ? AND plan_id = ? AND status = 'pending'
                """,
                (user_id, plan_id),
            ).fetchall()
        existing_titles = {str(row["title"]).casefold() for row in rows}
        for phase, actions in (
            ("7天行动", action_plan.seven_day),
            ("30天行动", action_plan.thirty_day),
            ("90天行动", action_plan.ninety_day),
        ):
            for action in actions:
                title = " ".join(action.split())
                if not title or title.casefold() in existing_titles:
                    continue
                created.append(
                    self.save(
                        user_id,
                        CareerTaskSaveRequest(
                            plan_id=plan_id,
                            title=title,
                            description=f"来自职业规划的{phase}建议",
                        ),
                    )
                )
                existing_titles.add(title.casefold())
        return created

    def get(self, user_id: str, task_id: str) -> CareerTaskRecord:
        with connect(self._database_path) as connection:
            row = connection.execute(
                "SELECT * FROM career_task WHERE id = ? AND user_id = ?", (task_id, user_id)
            ).fetchone()
        if row is None:
            raise CareerTaskNotFoundError
        return self._from_row(row)

    @staticmethod
    def _from_row(row) -> CareerTaskRecord:
        return CareerTaskRecord(
            id=str(row["id"]),
            plan_id=str(row["plan_id"]),
            title=str(row["title"]),
            description=str(row["description"]),
            due_date=row["due_date"],
            status=str(row["status"]),
            link_to_application_id=row["link_to_application_id"],
            link_to_evidence_id=row["link_to_evidence_id"],
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )
