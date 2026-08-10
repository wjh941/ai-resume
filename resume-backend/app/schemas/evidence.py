from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


EvidenceKind = Literal[
    "coursework",
    "project",
    "activity",
    "internship",
    "employment",
]


def _normalize_text(value: str, field_name: str, maximum: int, *, required: bool) -> str:
    normalized = " ".join(value.split())
    if required and not normalized:
        raise ValueError(f"{field_name} must not be blank")
    if len(normalized) > maximum:
        raise ValueError(f"{field_name} is too long")
    return normalized


class ResumeEvidenceSaveRequest(BaseModel):
    id: str | None = None
    client_id: str = Field(min_length=1, max_length=120)
    kind: EvidenceKind
    title: str = Field(min_length=1, max_length=160)
    context: str = Field(default="", max_length=2_000)
    actions: str = Field(min_length=1, max_length=4_000)
    outcome: str = Field(default="", max_length=2_000)
    proof_note: str = Field(default="", max_length=1_000)
    verified: bool = False

    @field_validator("id", "client_id", "title", "context", "actions", "outcome", "proof_note")
    @classmethod
    def normalize_text_fields(cls, value: str | None, info) -> str | None:
        if value is None:
            return None
        limits = {
            "id": (120, False),
            "client_id": (120, True),
            "title": (160, True),
            "context": (2_000, False),
            "actions": (4_000, True),
            "outcome": (2_000, False),
            "proof_note": (1_000, False),
        }
        maximum, required = limits[info.field_name]
        return _normalize_text(value, info.field_name, maximum, required=required)


class ResumeEvidence(ResumeEvidenceSaveRequest):
    id: str
    created_at: str
    updated_at: str
