from __future__ import annotations

import json
from pathlib import Path

from app.db import connect
from app.schemas.career import (
    MajorSuggestion,
    RoleFamilySummary,
    RoleProfile,
    RoleSuggestion,
)
from app.services.career_catalog import ROLE_FAMILIES
from app.services.job_cache import normalize_role_name


class CareerCatalogRepository:
    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path

    def list_families(self) -> list[RoleFamilySummary]:
        with connect(self._database_path) as connection:
            rows = connection.execute(
                """
                SELECT family, COUNT(*) AS role_count
                FROM role_profile
                GROUP BY family
                """
            ).fetchall()

        counts = {str(row["family"]): int(row["role_count"]) for row in rows}
        return [
            RoleFamilySummary(
                name=family["name"],
                description=family["description"],
                role_count=counts.get(family["name"], 0),
            )
            for family in ROLE_FAMILIES
        ]

    def search_roles(self, query: str, limit: int = 12) -> list[RoleSuggestion]:
        normalized_query = normalize_role_name(query)
        if not normalized_query or limit <= 0:
            return []

        with connect(self._database_path) as connection:
            rows = connection.execute(
                """
                SELECT role_name, family, aliases_json, description
                FROM role_profile
                ORDER BY family ASC, role_name ASC
                """
            ).fetchall()

        matches: list[tuple[int, str, RoleSuggestion]] = []
        for row in rows:
            role_name = str(row["role_name"])
            aliases = [
                normalize_role_name(value)
                for value in json.loads(str(row["aliases_json"]))
            ]
            score = _match_score(
                normalized_query,
                normalize_role_name(role_name),
                aliases,
                normalize_role_name(str(row["family"])),
            )
            if score is None:
                continue
            matches.append(
                (
                    score,
                    role_name,
                    RoleSuggestion(
                        role_name=role_name,
                        family=str(row["family"]),
                        description=str(row["description"]),
                    ),
                )
            )

        matches.sort(key=lambda item: (item[0], item[1]))
        return [item[2] for item in matches[:limit]]

    def search_majors(self, query: str, limit: int = 12) -> list[MajorSuggestion]:
        normalized_query = normalize_role_name(query)
        if not normalized_query or limit <= 0:
            return []

        with connect(self._database_path) as connection:
            rows = connection.execute(
                """
                SELECT major_name, category, aliases_json, related_families_json
                FROM major_catalog
                ORDER BY major_name ASC
                """
            ).fetchall()

        matches: list[tuple[int, str, MajorSuggestion]] = []
        for row in rows:
            major_name = str(row["major_name"])
            aliases = [
                normalize_role_name(value)
                for value in json.loads(str(row["aliases_json"]))
            ]
            score = _match_score(
                normalized_query,
                normalize_role_name(major_name),
                aliases,
                normalize_role_name(str(row["category"])),
            )
            if score is None:
                continue
            matches.append(
                (
                    score,
                    major_name,
                    MajorSuggestion(
                        major_name=major_name,
                        category=str(row["category"]),
                        related_families=json.loads(str(row["related_families_json"])),
                    ),
                )
            )

        matches.sort(key=lambda item: (item[0], item[1]))
        return [item[2] for item in matches[:limit]]

    def list_roles(self) -> list[RoleProfile]:
        with connect(self._database_path) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM role_profile
                ORDER BY family ASC, role_name ASC
                """
            ).fetchall()
        return [self._to_role_profile(row) for row in rows]

    @staticmethod
    def _to_role_profile(row) -> RoleProfile:
        return RoleProfile(
            role_name=str(row["role_name"]),
            family=str(row["family"]),
            aliases=json.loads(str(row["aliases_json"])),
            recommended_majors=json.loads(str(row["recommended_majors_json"])),
            adjacent_majors=json.loads(str(row["adjacent_majors_json"])),
            relevant_courses=json.loads(str(row["relevant_courses_json"])),
            required_skills=json.loads(str(row["required_skills_json"])),
            entry_skills=json.loads(str(row["entry_skills_json"])),
            alternative_roles=json.loads(str(row["alternative_roles_json"])),
            internship_roles=json.loads(str(row["internship_roles_json"])),
            entry_difficulty=int(row["entry_difficulty"]),
            industry_tags=json.loads(str(row["industry_tags_json"])),
            description=str(row["description"]),
        )


def _match_score(
    query: str,
    name: str,
    aliases: list[str],
    category: str,
) -> int | None:
    if name == query:
        return 0
    if name.startswith(query):
        return 1
    if query in name:
        return 2
    if any(alias.startswith(query) for alias in aliases):
        return 3
    if any(query in alias for alias in aliases):
        return 4
    if category.startswith(query) or query in category:
        return 5
    return None
