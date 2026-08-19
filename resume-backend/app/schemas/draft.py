from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.schemas.job import JobIntelligence
from app.schemas.resume import ResumePayload


class DraftSaveRequest(BaseModel):
    id: str | None = None
    job_title: str
    template_id: Literal["business", "technology", "graduate", "analytics"]
    resume: ResumePayload
    job_intelligence: JobIntelligence | None = None


class DraftCopyRequest(BaseModel):
    """复制归属由 JWT 决定，保留空模型以兼容现有 POST 路由。"""


class DraftVersionCreateRequest(BaseModel):
    note: str = Field(default="", max_length=240)

    @field_validator("note")
    @classmethod
    def normalize_note(cls, value: str) -> str:
        return " ".join(value.split())
