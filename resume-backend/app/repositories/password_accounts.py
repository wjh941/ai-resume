from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from app.db import DatabaseTarget, connect


class PasswordAccountExistsError(Exception):
    pass


@dataclass(frozen=True)
class PasswordAccountRecord:
    account: str
    user_id: str
    password_hash: str
    created_at: str
    last_login: str


class PasswordAccountRepository:
    def __init__(self, database_target: DatabaseTarget) -> None:
        self._database_target = database_target

    def exists(self, account: str) -> bool:
        return self.get(account) is not None

    def create(self, account: str, user_id: str, password_hash: str) -> PasswordAccountRecord:
        now = datetime.now(timezone.utc).isoformat()
        with connect(self._database_target) as connection:
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO password_account
                (account, user_id, password_hash, created_at, last_login)
                VALUES (?, ?, ?, ?, ?)
                """,
                (account, user_id, password_hash, now, now),
            )
            if cursor.rowcount != 1:
                raise PasswordAccountExistsError(account)
            row = connection.execute(
                "SELECT * FROM password_account WHERE account = ?", (account,)
            ).fetchone()
        if row is None:
            raise PasswordAccountExistsError(account)
        return self._from_row(row)

    def get(self, account: str) -> PasswordAccountRecord | None:
        with connect(self._database_target) as connection:
            row = connection.execute(
                "SELECT * FROM password_account WHERE account = ?", (account,)
            ).fetchone()
        return self._from_row(row) if row is not None else None

    def get_by_user_id(self, user_id: str) -> PasswordAccountRecord | None:
        with connect(self._database_target) as connection:
            row = connection.execute(
                "SELECT * FROM password_account WHERE user_id = ?", (user_id,)
            ).fetchone()
        return self._from_row(row) if row is not None else None

    def update_last_login(self, account: str) -> None:
        with connect(self._database_target) as connection:
            connection.execute(
                "UPDATE password_account SET last_login = ? WHERE account = ?",
                (datetime.now(timezone.utc).isoformat(), account),
            )

    @staticmethod
    def _from_row(row) -> PasswordAccountRecord:
        return PasswordAccountRecord(
            account=str(row["account"]),
            user_id=str(row["user_id"]),
            password_hash=str(row["password_hash"]),
            created_at=str(row["created_at"]),
            last_login=str(row["last_login"]),
        )
