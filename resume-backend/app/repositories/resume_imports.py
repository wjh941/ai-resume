from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json

from app.db import DatabaseTarget, connect


@dataclass(frozen=True)
class ResumeImportRecord:
    id: str
    status: str
    original_filename: str
    parsed_resume: dict[str, object]

    def as_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "status": self.status,
            "original_filename": self.original_filename,
            "parsed_resume": self.parsed_resume,
        }


class ResumeImportRepository:
    def __init__(self, database_target: DatabaseTarget) -> None:
        self._database_target = database_target

    def create(
        self,
        import_id: str,
        user_id: str,
        draft_id: str,
        stored_filename: str,
        original_filename: str,
        content_type: str,
        byte_size: int,
        parsed_resume: dict[str, object],
    ) -> ResumeImportRecord:
        with connect(self._database_target) as connection:
            connection.execute(
                """
                INSERT INTO resume_import
                (id, user_id, draft_id, stored_filename, original_filename, content_type,
                 byte_size, status, parsed_resume_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'parsed_mock', ?, ?)
                """,
                (
                    import_id,
                    user_id,
                    draft_id,
                    stored_filename,
                    original_filename,
                    content_type,
                    byte_size,
                    json.dumps(parsed_resume, ensure_ascii=False),
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
        return ResumeImportRecord(import_id, "parsed_mock", original_filename, parsed_resume)
