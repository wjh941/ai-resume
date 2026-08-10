from __future__ import annotations

from pydantic import BaseModel, Field


class KnowledgebaseRoleInput(BaseModel):
    role_name: str = Field(min_length=1, max_length=120)
    family: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=1000)


class KnowledgebaseRole(KnowledgebaseRoleInput):
    catalog_origin: str


class KnowledgeSyncSummary(BaseModel):
    run_id: int
    mode: str
    status: str
    added_roles: int = 0
    added_majors: int = 0
    skipped_rows: int = 0
    errors: list[str] = []


class OfficialDatasetSource(BaseModel):
    source_key: str
    display_name: str
    direct_url: str | None = None
    allowed_hosts: list[str]
    file_format: str
    parser_kind: str
    enabled: bool
    disabled_reason: str | None = None