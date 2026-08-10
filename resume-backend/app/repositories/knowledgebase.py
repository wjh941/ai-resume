from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from app.db import connect
from app.schemas.knowledgebase import (
    KnowledgebaseRole,
    KnowledgebaseRoleInput,
    KnowledgeSyncSummary,
    OfficialDatasetSource,
)


class KnowledgebaseRoleNotFoundError(Exception):
    pass


class KnowledgebaseRepository:
    """Owns editable catalog rows and preserves provenance during system imports."""

    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path

    def list_sources(self) -> list[OfficialDatasetSource]:
        with connect(self._database_path) as connection:
            rows = connection.execute(
                """
                SELECT source_key, display_name, direct_url, allowed_hosts_json,
                       file_format, parser_kind, enabled, disabled_reason
                FROM official_dataset_source
                ORDER BY source_key ASC
                """
            ).fetchall()
        if not rows:
            return [
                OfficialDatasetSource(
                    source_key="moe-major-directory",
                    display_name="教育部高校专业目录",
                    allowed_hosts=["moe.gov.cn"],
                    file_format="json",
                    parser_kind="major",
                    enabled=False,
                    disabled_reason="尚未登记可核验的官方 CSV/JSON 直链，禁止解析公告网页或 PDF。",
                ),
                OfficialDatasetSource(
                    source_key="mohrss-occupation-classification",
                    display_name="人社职业分类",
                    allowed_hosts=["mohrss.gov.cn"],
                    file_format="json",
                    parser_kind="occupation",
                    enabled=False,
                    disabled_reason="尚未登记可核验的官方 CSV/JSON 直链，禁止解析公告网页或 PDF。",
                ),
            ]
        return [
            OfficialDatasetSource(
                source_key=str(row["source_key"]),
                display_name=str(row["display_name"]),
                direct_url=str(row["direct_url"]) if row["direct_url"] else None,
                allowed_hosts=json.loads(str(row["allowed_hosts_json"])),
                file_format=str(row["file_format"]),
                parser_kind=str(row["parser_kind"]),
                enabled=bool(row["enabled"]),
                disabled_reason=str(row["disabled_reason"]) if row["disabled_reason"] else None,
            )
            for row in rows
        ]

    def list_enabled_sources(self) -> list[OfficialDatasetSource]:
        return [source for source in self.list_sources() if source.enabled and source.direct_url]

    def upsert_system_role(
        self,
        *,
        role_name: str,
        family: str,
        source_key: str,
        source_version: str,
        source_url: str,
    ) -> bool:
        role_name = role_name.strip()
        family = family.strip() or "其他"
        if not role_name:
            return False
        with connect(self._database_path) as connection:
            existing = connection.execute(
                "SELECT catalog_origin FROM role_profile WHERE role_name = ?", (role_name,)
            ).fetchone()
            if existing is not None and str(existing["catalog_origin"]) == "manual":
                return False
            aliases_json = json.dumps([role_name], ensure_ascii=False)
            empty_json = "[]"
            connection.execute(
                """
                INSERT INTO role_profile (
                    role_name, family, aliases_json, recommended_majors_json,
                    adjacent_majors_json, relevant_courses_json, required_skills_json,
                    entry_skills_json, alternative_roles_json, internship_roles_json,
                    entry_difficulty, industry_tags_json, description, catalog_origin,
                    source_key, source_version, source_url, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'official_dataset', ?, ?, ?, datetime('now'))
                ON CONFLICT(role_name) DO UPDATE SET
                    family = excluded.family,
                    aliases_json = excluded.aliases_json,
                    catalog_origin = excluded.catalog_origin,
                    source_key = excluded.source_key,
                    source_version = excluded.source_version,
                    source_url = excluded.source_url,
                    updated_at = excluded.updated_at
                """,
                (
                    role_name, family, aliases_json, empty_json, empty_json, empty_json,
                    empty_json, empty_json, empty_json, empty_json, 1, empty_json,
                    f"来自官方静态数据集：{source_key}", source_key, source_version, source_url,
                ),
            )
            connection.execute(
                """
                INSERT INTO job_catalog (role_name, category, aliases_json, sort_order)
                VALUES (?, ?, ?, 500000)
                ON CONFLICT(role_name) DO UPDATE SET
                    category = excluded.category,
                    aliases_json = excluded.aliases_json
                """,
                (role_name, family, aliases_json),
            )
        return existing is None
    def create_manual_role(self, payload: KnowledgebaseRoleInput) -> KnowledgebaseRole:
        role_name = payload.role_name.strip()
        family = payload.family.strip()
        description = payload.description.strip()
        with connect(self._database_path) as connection:
            existing = connection.execute(
                "SELECT catalog_origin FROM role_profile WHERE role_name = ?",
                (role_name,),
            ).fetchone()
            if existing is not None and str(existing["catalog_origin"]) != "manual":
                raise ValueError("系统标准岗位不可由手工新增接口覆盖")

            aliases_json = json.dumps([role_name], ensure_ascii=False)
            empty_json = "[]"
            connection.execute(
                """
                INSERT INTO role_profile (
                    role_name, family, aliases_json, recommended_majors_json,
                    adjacent_majors_json, relevant_courses_json, required_skills_json,
                    entry_skills_json, alternative_roles_json, internship_roles_json,
                    entry_difficulty, industry_tags_json, description, catalog_origin
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'manual')
                ON CONFLICT(role_name) DO UPDATE SET
                    family = excluded.family,
                    description = excluded.description,
                    aliases_json = excluded.aliases_json
                """,
                (
                    role_name,
                    family,
                    aliases_json,
                    empty_json,
                    empty_json,
                    empty_json,
                    empty_json,
                    empty_json,
                    empty_json,
                    empty_json,
                    1,
                    empty_json,
                    description,
                ),
            )
            connection.execute(
                """
                INSERT INTO job_catalog (role_name, category, aliases_json, sort_order)
                VALUES (?, ?, ?, 999999)
                ON CONFLICT(role_name) DO UPDATE SET
                    category = excluded.category,
                    aliases_json = excluded.aliases_json
                """,
                (role_name, family, aliases_json),
            )
        return KnowledgebaseRole(
            role_name=role_name,
            family=family,
            description=description,
            catalog_origin="manual",
        )

    def get_role(self, role_name: str) -> KnowledgebaseRole:
        with connect(self._database_path) as connection:
            row = connection.execute(
                """
                SELECT role_name, family, description, catalog_origin
                FROM role_profile
                WHERE role_name = ?
                """,
                (role_name,),
            ).fetchone()
        if row is None:
            raise KnowledgebaseRoleNotFoundError(role_name)
        return KnowledgebaseRole(
            role_name=str(row["role_name"]),
            family=str(row["family"]),
            description=str(row["description"]),
            catalog_origin=str(row["catalog_origin"]),
        )

    def create_sync_run(self, mode: str) -> int:
        with connect(self._database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO knowledge_sync_run (
                    mode, status, started_at, errors_json
                ) VALUES (?, 'running', datetime('now'), '[]')
                """,
                (mode,),
            )
            return int(cursor.lastrowid)

    def complete_sync_run(
        self,
        run_id: int,
        *,
        status: str,
        added_roles: int = 0,
        added_majors: int = 0,
        skipped_rows: int = 0,
        errors: Iterable[str] = (),
    ) -> KnowledgeSyncSummary:
        error_list = list(errors)
        with connect(self._database_path) as connection:
            connection.execute(
                """
                UPDATE knowledge_sync_run
                SET status = ?, completed_at = datetime('now'), added_roles = ?,
                    added_majors = ?, skipped_rows = ?, errors_json = ?
                WHERE id = ?
                """,
                (
                    status,
                    added_roles,
                    added_majors,
                    skipped_rows,
                    json.dumps(error_list, ensure_ascii=False),
                    run_id,
                ),
            )
        return KnowledgeSyncSummary(
            run_id=run_id,
            mode="official",
            status=status,
            added_roles=added_roles,
            added_majors=added_majors,
            skipped_rows=skipped_rows,
            errors=error_list,
        )

