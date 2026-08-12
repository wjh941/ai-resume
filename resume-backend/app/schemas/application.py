from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator


ApplicationStatus = Literal[
    "saved",
    "applied",
    "screening",
    "interview",
    "offer",
    "rejected",
    "closed",
]


def _normalize(value: str, maximum: int, *, required: bool) -> str:
    normalized = " ".join(value.split())
    if required and not normalized:
        raise ValueError("text must not be blank")
    if len(normalized) > maximum:
        raise ValueError("text is too long")
    return normalized


class ApplicationSaveRequest(BaseModel):
    id: str | None = None
    client_id: str = Field(min_length=1, max_length=120)
    company: str = Field(default="[待确认]", max_length=200)
    role_name: str = Field(min_length=1, max_length=160)
    city: str = Field(default="", max_length=120)
    source: str = Field(default="", max_length=120)
    status: ApplicationStatus = "saved"
    applied_at: date | None = None
    next_action_at: date | None = None
    interview_notes: str = Field(default="", max_length=8_000)
    draft_id: str | None = Field(default=None, max_length=120)
    notes: str = Field(default="", max_length=4_000)

    @field_validator(
        "id",
        "client_id",
        "company",
        "role_name",
        "city",
        "source",
        "interview_notes",
        "draft_id",
        "notes",
    )
    @classmethod
    def normalize_fields(cls, value: str | None, info) -> str | None:
        if value is None:
            return None
        limits = {
            "id": 120,
            "client_id": 120,
            "company": 200,
            "role_name": 160,
            "city": 120,
            "source": 120,
            "interview_notes": 8_000,
            "draft_id": 120,
            "notes": 4_000,
        }
        required = info.field_name in {"client_id", "role_name"}
        normalized = _normalize(value, limits[info.field_name], required=required)
        if info.field_name == "company" and not normalized:
            return "[待确认]"
        return normalized


class ApplicationRecord(ApplicationSaveRequest):
    id: str
    created_at: str
    updated_at: str
