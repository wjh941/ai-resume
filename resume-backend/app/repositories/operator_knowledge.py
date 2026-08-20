from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.db import DatabaseTarget, connect
from app.schemas.knowledgebase import OperatorKnowledgeCreate, OperatorKnowledgeUpdate


class OperatorKnowledgeNotFoundError(Exception):
    pass


class OperatorKnowledgeRepository:
    def __init__(self, database_target: DatabaseTarget) -> None:
        self._database_target = database_target

    def list_items(self) -> list[dict[str, object]]:
        with connect(self._database_target) as connection:
            rows = connection.execute(
                "SELECT * FROM knowledge_item ORDER BY updated_at DESC, id DESC"
            ).fetchall()
        return [self._item(row) for row in rows]

    def create(self, user_id: str, payload: OperatorKnowledgeCreate) -> dict[str, object]:
        item_id = str(uuid4())
        now = datetime.now(timezone.utc).isoformat()
        title = payload.title.strip()
        content = payload.content.strip()
        with connect(self._database_target) as connection:
            connection.execute(
                """
                INSERT INTO knowledge_item
                (id, title, content, status, current_version, created_by, created_at, updated_at)
                VALUES (?, ?, ?, ?, 1, ?, ?, ?)
                """,
                (item_id, title, content, payload.status, user_id, now, now),
            )
            self._create_version(connection, item_id, 1, title, content, payload.status, user_id, now)
            row = connection.execute("SELECT * FROM knowledge_item WHERE id = ?", (item_id,)).fetchone()
        return self._item(row)

    def update(
        self,
        user_id: str,
        item_id: str,
        payload: OperatorKnowledgeUpdate,
    ) -> dict[str, object]:
        with connect(self._database_target) as connection:
            current = connection.execute("SELECT * FROM knowledge_item WHERE id = ?", (item_id,)).fetchone()
            if current is None:
                raise OperatorKnowledgeNotFoundError(item_id)
            title = payload.title.strip() if payload.title is not None else str(current["title"])
            content = payload.content.strip() if payload.content is not None else str(current["content"])
            status = payload.status if payload.status is not None else str(current["status"])
            version = int(current["current_version"]) + 1
            now = datetime.now(timezone.utc).isoformat()
            connection.execute(
                """
                UPDATE knowledge_item
                SET title = ?, content = ?, status = ?, current_version = ?, updated_at = ?
                WHERE id = ?
                """,
                (title, content, status, version, now, item_id),
            )
            self._create_version(connection, item_id, version, title, content, status, user_id, now)
            row = connection.execute("SELECT * FROM knowledge_item WHERE id = ?", (item_id,)).fetchone()
        return self._item(row)

    def list_versions(self, item_id: str) -> list[dict[str, object]]:
        with connect(self._database_target) as connection:
            rows = connection.execute(
                """
                SELECT version, title, content, status, created_at
                FROM knowledge_item_version WHERE item_id = ?
                ORDER BY version DESC
                """,
                (item_id,),
            ).fetchall()
        if not rows:
            raise OperatorKnowledgeNotFoundError(item_id)
        return [
            {
                "version": int(row["version"]),
                "title": str(row["title"]),
                "content": str(row["content"]),
                "status": str(row["status"]),
                "created_at": str(row["created_at"]),
            }
            for row in rows
        ]

    def restore_version(self, user_id: str, item_id: str, version: int) -> dict[str, object]:
        with connect(self._database_target) as connection:
            source = connection.execute(
                """
                SELECT title, content, status FROM knowledge_item_version
                WHERE item_id = ? AND version = ?
                """,
                (item_id, version),
            ).fetchone()
            current = connection.execute("SELECT current_version FROM knowledge_item WHERE id = ?", (item_id,)).fetchone()
            if source is None or current is None:
                raise OperatorKnowledgeNotFoundError(item_id)
            next_version = int(current["current_version"]) + 1
            now = datetime.now(timezone.utc).isoformat()
            connection.execute(
                """
                UPDATE knowledge_item
                SET title = ?, content = ?, status = ?, current_version = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    source["title"], source["content"], source["status"], next_version, now, item_id,
                ),
            )
            self._create_version(
                connection,
                item_id,
                next_version,
                str(source["title"]),
                str(source["content"]),
                str(source["status"]),
                user_id,
                now,
            )
            row = connection.execute("SELECT * FROM knowledge_item WHERE id = ?", (item_id,)).fetchone()
        return self._item(row)

    @staticmethod
    def _create_version(connection, item_id: str, version: int, title: str, content: str, status: str, user_id: str, created_at: str) -> None:
        connection.execute(
            """
            INSERT INTO knowledge_item_version
            (id, item_id, version, title, content, status, created_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (str(uuid4()), item_id, version, title, content, status, user_id, created_at),
        )

    @staticmethod
    def _item(row) -> dict[str, object]:
        return {
            "id": str(row["id"]),
            "title": str(row["title"]),
            "content": str(row["content"]),
            "status": str(row["status"]),
            "version": int(row["current_version"]),
            "created_at": str(row["created_at"]),
            "updated_at": str(row["updated_at"]),
        }
