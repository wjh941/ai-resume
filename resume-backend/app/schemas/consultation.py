from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.schemas.job import JobIntelligence

IdentityCode = Literal["1", "2", "3", "4", "5"]
AdviceTopic = Literal[
    "simulation_interview",
    "salary_negotiation",
    "contract_pitfalls",
    "career_planning",
    "certificate_recommendation",
    "role_comparison",
    "written_test",
    "job_channels",
    "scam_screening",
]

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
    custom_requirement: str | None = Field(default=None, max_length=2_000)

    @field_validator("role_name")
    @classmethod
    def require_non_blank_role(cls, value: str) -> str:
        return _non_blank(value, "role_name")

    @field_validator("custom_requirement")
    @classmethod
    def normalize_optional_custom_requirement(cls, value: str | None) -> str | None:
        normalized = " ".join(value.split()) if value else ""
        return normalized or None


class ResumeReviewRequest(BaseModel):
    resume_text: str = Field(min_length=1, max_length=20_000)
    identity_code: IdentityCode
    role_name: str | None = Field(default=None, max_length=200)
    custom_requirement: str | None = Field(default=None, max_length=2_000)

    @field_validator("resume_text")
    @classmethod
    def require_non_blank_resume_text(cls, value: str) -> str:
        return _non_blank(value, "resume_text")

    @field_validator("role_name")
    @classmethod
    def normalize_optional_role(cls, value: str | None) -> str | None:
        return _non_blank(value, "role_name") if value is not None else None

    @field_validator("custom_requirement")
    @classmethod
    def normalize_optional_custom_requirement(cls, value: str | None) -> str | None:
        normalized = " ".join(value.split()) if value else ""
        return normalized or None


class AdviceRequest(BaseModel):
    identity_code: IdentityCode
    topic: AdviceTopic
    role_name: str | None = Field(default=None, max_length=200)
    question: str | None = Field(default=None, max_length=2_000)

    @field_validator("role_name", "question")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        return _non_blank(value, "text") if value is not None else None


class ConsultationSection(BaseModel):
    order: int = Field(ge=1)
    title: str = Field(min_length=1)
    items: list[str] = Field(min_length=1)


class IdentityPlan(BaseModel):
    title: str = Field(min_length=1)
    sections: list[ConsultationSection] = Field(min_length=4)


class CareerGrowthStage(BaseModel):
    stage: str = Field(min_length=1)
    role_name: str = Field(min_length=1)
    years_reference: str = Field(min_length=1)
    core_skills: list[str] = Field(min_length=1)
    responsibilities: list[str] = Field(min_length=1)
    assessment_criteria: list[str] = Field(min_length=1)


class CareerGrowthRoute(BaseModel):
    title: str = Field(min_length=1)
    stages: list[CareerGrowthStage] = Field(min_length=3, max_length=3)


class PrioritySkillGap(BaseModel):
    skill_name: str = Field(min_length=1)
    learning_direction: str = Field(min_length=1)
    project_practice: str = Field(min_length=1)
    practice_task: str = Field(min_length=1)


class JobMatchReport(BaseModel):
    score: int = Field(ge=0, le=100)
    score_basis: list[str] = Field(min_length=1)
    matching_advantages: list[str] = Field(min_length=1)
    missing_skills: list[str] = Field(min_length=1)
    priority_gaps: list[PrioritySkillGap] = Field(min_length=1)


class JobConsultationResponse(BaseModel):
    identity_code: IdentityCode
    identity_label: str
    job_intelligence: JobIntelligence
    job_analysis_sections: list[ConsultationSection] = Field(min_length=9, max_length=9)
    identity_plan: IdentityPlan
    follow_up_question: str
    market_notice: str
    career_growth_route: CareerGrowthRoute
    custom_requirement_notes: list[str] = Field(default_factory=list)


class ResumeReviewResponse(BaseModel):
    identity_code: IdentityCode
    identity_label: str
    issues: list[str] = Field(min_length=1)
    rewrite_examples: list[str] = Field(min_length=1)
    keywords: list[str] = Field(min_length=1)
    optimized_resume_text: str = Field(min_length=1)
    interview_intro: str = Field(min_length=1)
    job_match_report: JobMatchReport
    custom_requirement_notes: list[str] = Field(default_factory=list)


class CareerAdviceResponse(BaseModel):
    identity_code: IdentityCode
    identity_label: str
    topic: AdviceTopic
    title: str = Field(min_length=1)
    sections: list[ConsultationSection] = Field(min_length=2)
