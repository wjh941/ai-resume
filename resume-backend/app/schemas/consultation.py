from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.schemas.job import JobIntelligence

IdentityCode = Literal["1", "2", "3", "4", "5"]

IDENTITY_LABELS: dict[IdentityCode, str] = {
    "1": "在校学生（寻找短期实习）",
    "2": "应届毕业生（秋招/春招）",
    "3": "在职人员（想跳槽）",
    "4": "无业待业（有工作经验空档期）",
    "5": "零基础跨行业转行",
}


def _non_blank(value: str, field_name: str) -> str:
    normalized = " ".join(value.split())
    if not normalized:
        raise ValueError(f"{field_name} must not be blank")
    return normalized


class JobConsultationRequest(BaseModel):
    role_name: str = Field(min_length=1, max_length=200)
    identity_code: IdentityCode

    @field_validator("role_name")
    @classmethod
    def require_non_blank_role(cls, value: str) -> str:
        return _non_blank(value, "role_name")


class ResumeReviewRequest(BaseModel):
    resume_text: str = Field(min_length=1, max_length=20_000)
    identity_code: IdentityCode
    role_name: str | None = Field(default=None, max_length=200)

    @field_validator("resume_text")
    @classmethod
    def require_non_blank_resume_text(cls, value: str) -> str:
        return _non_blank(value, "resume_text")

    @field_validator("role_name")
    @classmethod
    def normalize_optional_role(cls, value: str | None) -> str | None:
        return _non_blank(value, "role_name") if value is not None else None


class ConsultationSection(BaseModel):
    order: int = Field(ge=1)
    title: str = Field(min_length=1)
    items: list[str] = Field(min_length=1)


class IdentityPlan(BaseModel):
    title: str = Field(min_length=1)
    sections: list[ConsultationSection] = Field(min_length=4)


class JobConsultationResponse(BaseModel):
    identity_code: IdentityCode
    identity_label: str
    job_intelligence: JobIntelligence
    job_analysis_sections: list[ConsultationSection] = Field(min_length=8, max_length=8)
    identity_plan: IdentityPlan
    follow_up_question: str


class ResumeReviewResponse(BaseModel):
    identity_code: IdentityCode
    identity_label: str
    issues: list[str] = Field(min_length=1)
    rewrite_examples: list[str] = Field(min_length=1)
    keywords: list[str] = Field(min_length=1)
