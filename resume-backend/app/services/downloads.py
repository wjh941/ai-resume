from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from app.db import connect
from app.schemas.exports import ExportResult


class DownloadNotFoundError(Exception):
    pass


@dataclass(frozen=True)
class DownloadFile:
    token: str
    path: Path
    filename: str
    expires_at: datetime


class DownloadService:
    def __init__(self, database_path: Path, temp_directory: Path, expire_minutes: int) -> None:
        self._database_path = database_path
        self._temp_directory = temp_directory.resolve()
        self._expire_minutes = expire_minutes

    def register(self, output_path: Path, filename: str) -> ExportResult:
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=self._expire_minutes)
        token = uuid4().hex
        with connect(self._database_path) as connection:
            connection.execute(
                """
                INSERT INTO download_file (token, file_path, filename, expires_at, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (token, str(output_path.resolve()), filename, expires_at.isoformat(), now.isoformat()),
            )
        return ExportResult(
            filename=filename,
            download_url=f"/downloads/{token}",
            expires_at=expires_at,
        )

    def resolve(self, token: str) -> DownloadFile:
        with connect(self._database_path) as connection:
            row = connection.execute(
                "SELECT token, file_path, filename, expires_at FROM download_file WHERE token = ?",
                (token,),
            ).fetchone()
        if row is None:
            raise DownloadNotFoundError

        expires_at = datetime.fromisoformat(row["expires_at"])
        output_path = Path(row["file_path"])
        if expires_at <= datetime.now(timezone.utc) or not output_path.is_file():
            self._delete_records([token])
            self._delete_file_if_owned(output_path)
            raise DownloadNotFoundError
        return DownloadFile(token, output_path, row["filename"], expires_at)

    def cleanup_expired(self) -> int:
        now = datetime.now(timezone.utc).isoformat()
        with connect(self._database_path) as connection:
            rows = connection.execute(
                "SELECT token, file_path FROM download_file WHERE expires_at <= ?",
                (now,),
            ).fetchall()
        self._delete_records([row["token"] for row in rows])
        for row in rows:
            self._delete_file_if_owned(Path(row["file_path"]))
        return len(rows)

    def _delete_records(self, tokens: list[str]) -> None:
        if not tokens:
            return
        placeholders = ", ".join("?" for _ in tokens)
        with connect(self._database_path) as connection:
            connection.execute(f"DELETE FROM download_file WHERE token IN ({placeholders})", tokens)

    def _delete_file_if_owned(self, path: Path) -> None:
        try:
            path.resolve().relative_to(self._temp_directory)
        except ValueError:
            return
        try:
            path.unlink(missing_ok=True)
        except OSError:
            return
