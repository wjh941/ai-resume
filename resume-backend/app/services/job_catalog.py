from __future__ import annotations

import json
from pathlib import Path

from app.db import connect
from app.schemas.job import JobSuggestion
from app.services.job_cache import normalize_role_name


class JobCatalog:
    """Searches the locally seeded role catalog used for type-ahead discovery."""

    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path

    def search(self, query: str, limit: int = 8) -> list[JobSuggestion]:
        normalized_query = normalize_role_name(query)
        if not normalized_query or limit <= 0:
            return []

        with connect(self._database_path) as connection:
            rows = connection.execute(
                """
                SELECT role_name, category, aliases_json, sort_order
                FROM job_catalog
                ORDER BY sort_order ASC, role_name ASC
                """
            ).fetchall()

        matches: list[tuple[int, int, JobSuggestion]] = []
        for row in rows:
            role_name = str(row["role_name"])
            normalized_role = normalize_role_name(role_name)
            aliases = [normalize_role_name(value) for value in json.loads(row["aliases_json"])]
            score = _match_score(normalized_query, normalized_role, aliases)
            if score is None:
                continue
            matches.append(
                (
                    score,
                    int(row["sort_order"]),
                    JobSuggestion(role_name=role_name, category=str(row["category"])),
                )
            )

        matches.sort(key=lambda item: (item[0], item[1], item[2].role_name))
        return [item[2] for item in matches[:limit]]


def _match_score(query: str, role_name: str, aliases: list[str]) -> int | None:
    if role_name == query:
        return 0
    if role_name.startswith(query):
        return 1
    if query in role_name:
        return 2
    if any(alias.startswith(query) for alias in aliases):
        return 3
    if any(query in alias for alias in aliases):
        return 4
    return None
