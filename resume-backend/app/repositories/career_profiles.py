from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

from app.db import connect
from app.schemas.career import CareerProfile, CareerProfilePayload


class CareerProfileNotFoundError(Exception):
    pass


class CareerProfileRepository:
    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path

    def save(self, user_id: str, profile: CareerProfilePayload) -> CareerProfile:
        now = datetime.now(timezone.utc).isoformat()
        with connect(self._database_path) as connection:
            values = (
                profile.identity_code,
                profile.major,
                profile.education_level,
                profile.graduation_year,
                _to_json(profile.city_preferences),
                profile.minimum_salary,
                _to_json(profile.industry_preferences),
                _to_json(profile.work_types),
                _to_json(profile.skills),
                profile.draft_id,
                now,
            )
            existing = connection.execute(
                "SELECT client_id FROM career_profile WHERE user_id = ?", (user_id,)
            ).fetchone()
            if existing is None:
                connection.execute(
                    """
                    INSERT INTO career_profile (
                        client_id, user_id, identity_code, major, education_level, graduation_year,
                        city_preferences_json, minimum_salary, industry_preferences_json,
                        work_types_json, skills_json, draft_id, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (user_id, user_id, *values),
                )
            else:
                connection.execute(
                    """
                    UPDATE career_profile
                    SET identity_code = ?, major = ?, education_level = ?, graduation_year = ?,
                        city_preferences_json = ?, minimum_salary = ?, industry_preferences_json = ?,
                        work_types_json = ?, skills_json = ?, draft_id = ?, updated_at = ?
                    WHERE user_id = ?
                    """,
                    (*values, user_id),
                )
        return self.get(user_id)

    def get(self, user_id: str) -> CareerProfile:
        with connect(self._database_path) as connection:
            row = connection.execute(
                "SELECT * FROM career_profile WHERE user_id = ?",
                (user_id,),
            ).fetchone()
        if row is None:
            raise CareerProfileNotFoundError
        return CareerProfile(
            identity_code=str(row["identity_code"]),
            major=str(row["major"]),
            education_level=str(row["education_level"]),
            graduation_year=row["graduation_year"],
            city_preferences=json.loads(str(row["city_preferences_json"])),
            minimum_salary=row["minimum_salary"],
            industry_preferences=json.loads(str(row["industry_preferences_json"])),
            work_types=json.loads(str(row["work_types_json"])),
            skills=json.loads(str(row["skills_json"])),
            draft_id=row["draft_id"],
            updated_at=str(row["updated_at"]),
        )


def _to_json(values: list[str]) -> str:
    return json.dumps(values, ensure_ascii=False)
