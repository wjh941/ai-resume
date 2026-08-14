from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.db import connect


class UserNotFoundError(Exception):
    pass


@dataclass(frozen=True)
class UserRecord:
    user_id: str
    phone: str
    token_version: int
    created_at: str
    last_login: str


class UserRepository:
    """本期 SQLite 用户仓储；业务仓储仅接收其 JWT 派生 user_id。"""

    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path

    def find_or_create_by_phone(self, phone: str) -> UserRecord:
        now = datetime.now(timezone.utc).isoformat()
        with connect(self._database_path) as connection:
            row = connection.execute(
                "SELECT * FROM users WHERE phone = ?", (phone,)
            ).fetchone()
            if row is None:
                user_id = str(uuid4())
                connection.execute(
                    """
                    INSERT INTO users (user_id, phone, token_version, created_at, last_login)
                    VALUES (?, ?, 1, ?, ?)
                    """,
                    (user_id, phone, now, now),
                )
                row = connection.execute(
                    "SELECT * FROM users WHERE user_id = ?", (user_id,)
                ).fetchone()
            else:
                connection.execute(
                    "UPDATE users SET last_login = ? WHERE user_id = ?", (now, row["user_id"])
                )
                row = connection.execute(
                    "SELECT * FROM users WHERE user_id = ?", (row["user_id"],)
                ).fetchone()
        if row is None:
            raise UserNotFoundError
        return self._from_row(row)

    def get(self, user_id: str) -> UserRecord:
        with connect(self._database_path) as connection:
            row = connection.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        if row is None:
            raise UserNotFoundError(user_id)
        return self._from_row(row)

    def invalidate_tokens(self, user_id: str) -> None:
        with connect(self._database_path) as connection:
            cursor = connection.execute(
                "UPDATE users SET token_version = token_version + 1 WHERE user_id = ?", (user_id,)
            )
        if cursor.rowcount == 0:
            raise UserNotFoundError(user_id)

    @staticmethod
    def _from_row(row) -> UserRecord:
        return UserRecord(
            user_id=str(row["user_id"]),
            phone=str(row["phone"]),
            token_version=int(row["token_version"]),
            created_at=str(row["created_at"]),
            last_login=str(row["last_login"]),
        )
