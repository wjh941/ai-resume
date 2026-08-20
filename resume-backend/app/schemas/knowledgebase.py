from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


OperatorKnowledgeStatus = Literal["active", "offline", "invalid"]


class OperatorKnowledgeCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=20_000)
    status: OperatorKnowledgeStatus = "active"


class OperatorKnowledgeUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = Field(default=None, min_length=1, max_length=20_000)
    status: OperatorKnowledgeStatus | None = None


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
