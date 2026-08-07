from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.schemas.resume import ResumePayload


class JobQueryRequest(BaseModel):
    role_name: str = Field(min_length=1, max_length=200)

    @field_validator("role_name")
    @classmethod
    def require_non_blank_role(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if not normalized:
            raise ValueError("role_name must not be blank")
        return normalized


class JobSuggestion(BaseModel):
    role_name: str
    category: str


class MarketSource(BaseModel):
    title: str
    url: str
    snippet: str
    published_date: str | None = None


class MarketSearchReport(BaseModel):
    enabled: bool
    provider: str
    notice: str
    results: list[MarketSource] = Field(default_factory=list)


class JobIntelligence(BaseModel):
    version: Literal[1] = 1
    role_name: str
    salary_by_experience: dict[str, str] = Field(default_factory=dict)
    responsibilities: list[str] = Field(default_factory=list)
    hard_requirements: list[str] = Field(default_factory=list)
    required_skills: list[str] = Field(default_factory=list)
    bonus_skills: list[str] = Field(default_factory=list)
    career_route: list[str] = Field(default_factory=list)


class ResumeRewriteRequest(BaseModel):
    resume: ResumePayload
    job: JobIntelligence
    mode: Literal["light", "deep"]
