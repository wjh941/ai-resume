from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO
import json
from pathlib import Path
import zipfile

from app.db import connect


class AccountPrivacyRepository:
    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path

    def export_archive(self, user_id: str) -> bytes:
        with connect(self._database_path) as connection:
            drafts = [self._draft_from_row(row) for row in connection.execute(
                "SELECT * FROM user_draft WHERE user_id = ? ORDER BY created_at, id", (user_id,)
            )]
            profile_row = connection.execute(
                "SELECT * FROM career_profile WHERE user_id = ?", (user_id,)
            ).fetchone()
            applications = [dict(row) for row in connection.execute(
                "SELECT * FROM application_tracker WHERE user_id = ? ORDER BY created_at, id", (user_id,)
            )]
        payload = {
            "format_version": 1,
            "resume_drafts": drafts,
            "career_profile": self._profile_from_row(profile_row),
            "applications": applications,
        }
        stream = BytesIO()
        with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("account-data.json", json.dumps(payload, ensure_ascii=False, indent=2))
        return stream.getvalue()

    def record_privacy_consent(self, user_id: str) -> str:
        now = datetime.now(timezone.utc).isoformat()
        with connect(self._database_path) as connection:
            connection.execute(
                "UPDATE users SET privacy_consent_at = COALESCE(privacy_consent_at, ?) WHERE user_id = ?",
                (now, user_id),
            )
        return now

    def soft_delete(self, user_id: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        anonymized_owner = f"deleted:{user_id}"
        with connect(self._database_path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                """
                UPDATE users
                SET phone = ?, is_deleted = 1, deleted_at = ?, token_version = token_version + 1
                WHERE user_id = ? AND is_deleted = 0
                """,
                (anonymized_owner, now, user_id),
            )
            connection.execute(
                "UPDATE user_draft SET user_id = NULL, client_id = ?, job_title = '[deleted]', payload_json = '{}' WHERE user_id = ?",
                (anonymized_owner, user_id),
            )
            connection.execute(
                """
                UPDATE career_profile
                SET user_id = NULL, identity_code = 'deleted', major = '[deleted]',
                    education_level = '[deleted]', graduation_year = NULL, city_preferences_json = '[]',
                    minimum_salary = NULL, industry_preferences_json = '[]', work_types_json = '[]',
                    skills_json = '[]', draft_id = NULL, updated_at = ?
                WHERE user_id = ?
                """,
                (now, user_id),
            )
            connection.execute(
                """
                UPDATE career_assessment
                SET user_id = NULL, answers_json = '{}', result_json = '{}', updated_at = ?
                WHERE user_id = ?
                """,
                (now, user_id),
            )
            connection.execute(
                """
                UPDATE application_tracker
                SET user_id = NULL, client_id = ?, company = '[deleted]', role_name = '[deleted]',
                    city = '', source = '', interview_notes = '', draft_id = NULL, notes = '', updated_at = ?
                WHERE user_id = ?
                """,
                (anonymized_owner, now, user_id),
            )
            connection.execute(
                """
                UPDATE resume_evidence
                SET user_id = NULL, client_id = ?, title = '[deleted]', context = '', actions = '',
                    outcome = '', proof_note = '', updated_at = ?
                WHERE user_id = ?
                """,
                (anonymized_owner, now, user_id),
            )
            connection.execute("DELETE FROM job_favorite WHERE user_id = ?", (user_id,))
            connection.execute("DELETE FROM job_match_subscription WHERE user_id = ?", (user_id,))
            connection.execute("DELETE FROM download_file WHERE user_id = ?", (user_id,))

    @staticmethod
    def _draft_from_row(row) -> dict[str, object]:
        snapshot = json.loads(str(row["payload_json"]))
        return {
            "id": str(row["id"]),
            "job_title": str(row["job_title"]),
            "template_id": str(row["template_id"]),
            "resume": snapshot.get("resume"),
            "job_intelligence": snapshot.get("job_intelligence"),
            "created_at": str(row["created_at"]),
            "updated_at": str(row["updated_at"]),
        }

    @staticmethod
    def _profile_from_row(row) -> dict[str, object] | None:
        if row is None:
            return None
        return {
            "identity_code": str(row["identity_code"]),
            "major": str(row["major"]),
            "education_level": str(row["education_level"]),
            "graduation_year": row["graduation_year"],
            "city_preferences": json.loads(str(row["city_preferences_json"])),
            "minimum_salary": row["minimum_salary"],
            "industry_preferences": json.loads(str(row["industry_preferences_json"])),
            "work_types": json.loads(str(row["work_types_json"])),
            "skills": json.loads(str(row["skills_json"])),
            "draft_id": row["draft_id"],
            "updated_at": str(row["updated_at"]),
        }
