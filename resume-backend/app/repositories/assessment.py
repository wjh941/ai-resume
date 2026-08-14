from __future__ import annotations

from datetime import date, datetime, timezone
import json
from pathlib import Path

from app.db import connect


class AssessmentNotFoundError(Exception):
    pass


class AssessmentRepository:
    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path

    def save(
        self,
        user_id: str,
        *,
        version: int,
        answers: dict[str, int],
        result: dict[str, object],
    ) -> dict[str, object]:
        updated_at = datetime.now(timezone.utc).isoformat()
        with connect(self._database_path) as connection:
            existing = connection.execute(
                "SELECT client_id FROM career_assessment WHERE user_id = ?", (user_id,)
            ).fetchone()
            values = (
                version,
                json.dumps(answers, ensure_ascii=False),
                json.dumps(result, ensure_ascii=False),
                updated_at,
            )
            if existing is None:
                connection.execute(
                    """
                    INSERT INTO career_assessment (
                        client_id, user_id, assessment_version, answers_json, result_json, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (user_id, user_id, *values),
                )
            else:
                connection.execute(
                    """
                    UPDATE career_assessment
                    SET assessment_version = ?, answers_json = ?, result_json = ?, updated_at = ?
                    WHERE user_id = ?
                    """,
                    (*values, user_id),
                )
        return self.get(user_id)

    def get(self, user_id: str) -> dict[str, object]:
        with connect(self._database_path) as connection:
            row = connection.execute(
                """
                SELECT assessment_version, answers_json, result_json, updated_at
                FROM career_assessment
                WHERE user_id = ?
                """,
                (user_id,),
            ).fetchone()
        if row is None:
            raise AssessmentNotFoundError(user_id)
        return {
            "version": int(row["assessment_version"]),
            "answers": json.loads(str(row["answers_json"])),
            "result": json.loads(str(row["result_json"])),
            "updated_at": str(row["updated_at"]),
        }

    def save_annual_insight(self, insight: dict[str, object]) -> dict[str, object]:
        normalized = self._normalize_annual_insight(insight)
        created_at = datetime.now(timezone.utc).isoformat()
        with connect(self._database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO annual_employment_insight (
                    year, scope, audience, category, title, content, source_label,
                    publication_date, confidence_note, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    normalized["year"],
                    normalized["scope"],
                    normalized["audience"],
                    normalized["category"],
                    normalized["title"],
                    normalized["content"],
                    normalized["source_label"],
                    normalized["publication_date"],
                    normalized["confidence_note"],
                    created_at,
                ),
            )
            row = connection.execute(
                """
                SELECT id, year, scope, audience, category, title, content, source_label,
                       publication_date, confidence_note, created_at
                FROM annual_employment_insight
                WHERE id = ?
                """,
                (cursor.lastrowid,),
            ).fetchone()
        return self._annual_insight_from_row(row)

    def list_annual_insights(self, year: int | None = None) -> list[dict[str, object]]:
        with connect(self._database_path) as connection:
            if year is None:
                rows = connection.execute(
                    """
                    SELECT id, year, scope, audience, category, title, content, source_label,
                           publication_date, confidence_note, created_at
                    FROM annual_employment_insight
                    ORDER BY year DESC, publication_date DESC, id DESC
                    """
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT id, year, scope, audience, category, title, content, source_label,
                           publication_date, confidence_note, created_at
                    FROM annual_employment_insight
                    WHERE year = ?
                    ORDER BY publication_date DESC, id DESC
                    """,
                    (year,),
                ).fetchall()
        return [self._annual_insight_from_row(row) for row in rows]

    @staticmethod
    def _normalize_annual_insight(insight: dict[str, object]) -> dict[str, object]:
        try:
            year = int(insight["year"])
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("Annual insight year is invalid") from error
        if not 2000 <= year <= 2100:
            raise ValueError("Annual insight year is invalid")

        normalized: dict[str, object] = {"year": year}
        for field, maximum in (
            ("scope", 80),
            ("audience", 80),
            ("category", 80),
            ("title", 160),
            ("content", 3000),
            ("source_label", 200),
            ("confidence_note", 300),
        ):
            value = " ".join(str(insight.get(field, "")).split())
            if not value or len(value) > maximum:
                raise ValueError(f"Annual insight {field} is invalid")
            normalized[field] = value

        publication_date = str(insight.get("publication_date", ""))
        try:
            normalized["publication_date"] = date.fromisoformat(publication_date).isoformat()
        except ValueError as error:
            raise ValueError("Annual insight publication_date is invalid") from error
        return normalized

    @staticmethod
    def _annual_insight_from_row(row: object) -> dict[str, object]:
        return {
            "id": int(row["id"]),
            "year": int(row["year"]),
            "scope": str(row["scope"]),
            "audience": str(row["audience"]),
            "category": str(row["category"]),
            "title": str(row["title"]),
            "content": str(row["content"]),
            "source_label": str(row["source_label"]),
            "publication_date": str(row["publication_date"]),
            "confidence_note": str(row["confidence_note"]),
            "created_at": str(row["created_at"]),
        }
