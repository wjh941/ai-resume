from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
import time
from uuid import uuid4

from app.db import connect
from app.schemas.exports import ExportResult


class DownloadNotFoundError(Exception):
    pass


class ExportPathError(Exception):
    pass


@dataclass(frozen=True)
class DownloadFile:
    token: str
    path: Path
    filename: str
    expires_at: datetime


class DownloadService:
    _GENERATED_EXPORT_SUFFIXES = frozenset({".docx", ".pdf", ".xlsx", ".zip"})

    def __init__(self, database_path: Path, temp_directory: Path, expire_minutes: int) -> None:
        self._database_path = database_path
        self._temp_directory = temp_directory.resolve()
        self._expire_minutes = expire_minutes

    def register(self, user_id: str, output_path: Path, filename: str) -> ExportResult:
        output_path = output_path.resolve()
        try:
            output_path.relative_to(self._temp_directory)
        except ValueError as error:
            raise ExportPathError("Export output path is outside controlled storage.") from error
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=self._expire_minutes)
        token = uuid4().hex
        with connect(self._database_path) as connection:
            connection.execute(
                """
                INSERT INTO download_file (token, user_id, file_path, filename, expires_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (token, user_id, str(output_path), filename, expires_at.isoformat(), now.isoformat()),
            )
        return ExportResult(
            filename=filename,
            download_url=f"/downloads/{token}",
            expires_at=expires_at,
        )

    def resolve(self, user_id: str, token: str) -> DownloadFile:
        with connect(self._database_path) as connection:
            row = connection.execute(
                "SELECT token, file_path, filename, expires_at FROM download_file WHERE token = ? AND user_id = ?",
                (token, user_id),
            ).fetchone()
        if row is None:
            raise DownloadNotFoundError

        expires_at = datetime.fromisoformat(row["expires_at"])
        output_path = Path(row["file_path"]).resolve()
        try:
            output_path.relative_to(self._temp_directory)
        except ValueError:
            self._delete_records([token])
            raise DownloadNotFoundError
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
        return len(rows) + self._cleanup_orphan_exports()

    def _cleanup_orphan_exports(self) -> int:
        if not self._temp_directory.is_dir():
            return 0
        cutoff = time.time() - self._expire_minutes * 60
        removed = 0
        for path in self._temp_directory.iterdir():
            if path.suffix.lower() not in self._GENERATED_EXPORT_SUFFIXES:
                continue
            try:
                if path.is_file() and path.stat().st_mtime <= cutoff:
                    path.unlink()
                    removed += 1
            except OSError:
                continue
        return removed

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
