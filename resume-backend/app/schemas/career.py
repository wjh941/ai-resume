from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.schemas.consultation import IdentityCode


MatchingLevel = Literal["high", "transferable", "needs_upskilling", "long_shot"]
RecommendationTier = Literal["stretch", "stable", "safe"]


def _normalize_text(value: str, field_name: str) -> str:
    normalized = " ".join(value.split())
    if not normalized:
        raise ValueError(f"{field_name} must not be blank")
    return normalized


def _normalize_list(values: list[str]) -> list[str]:
    items: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = " ".join(value.split())
        key = normalized.casefold()
        if normalized and key not in seen:
            seen.add(key)
            items.append(normalized)
    return items


class CareerProfilePayload(BaseModel):
    client_id: str = Field(min_length=1, max_length=120)
    identity_code: IdentityCode
    major: str = Field(min_length=1, max_length=120)
    education_level: str = Field(min_length=1, max_length=60)
    graduation_year: int | None = Field(default=None, ge=1990, le=2100)
    city_preferences: list[str] = Field(default_factory=list, max_length=20)
    minimum_salary: str | None = Field(default=None, max_length=80)
    industry_preferences: list[str] = Field(default_factory=list, max_length=20)
    work_types: list[str] = Field(default_factory=list, max_length=10)
    skills: list[str] = Field(default_factory=list, max_length=80)
    draft_id: str | None = Field(default=None, max_length=120)

    @field_validator("client_id", "major", "education_level")
    @classmethod
    def normalize_required_text(cls, value: str) -> str:
        return _normalize_text(value, "text")

    @field_validator("minimum_salary", "draft_id")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        return _normalize_text(value, "text") if value is not None else None

    @field_validator("city_preferences", "industry_preferences", "work_types", "skills")
    @classmethod
    def normalize_values(cls, values: list[str]) -> list[str]:
        return _normalize_list(values)


class CareerProfile(CareerProfilePayload):
    updated_at: str


class RoleFamilySummary(BaseModel):
    name: str
    description: str
    role_count: int = Field(ge=0)


class RoleSuggestion(BaseModel):
    role_name: str
    family: str
    description: str


class MajorSuggestion(BaseModel):
    major_name: str
    category: str
    related_families: list[str]


class RoleProfile(BaseModel):
    role_name: str
    family: str
    aliases: list[str]
    recommended_majors: list[str]
    adjacent_majors: list[str]
    relevant_courses: list[str]
    required_skills: list[str]
    entry_skills: list[str]
    alternative_roles: list[str]
    internship_roles: list[str]
    entry_difficulty: int = Field(ge=1, le=5)
    industry_tags: list[str]
    description: str


class ScoreBreakdown(BaseModel):
    key: str
    label: str
    score: float = Field(ge=0)
    max_score: float = Field(gt=0)
    reason: str
    missing_evidence: list[str] = Field(default_factory=list)


class CareerRecommendation(BaseModel):
    role: RoleProfile
    tier: RecommendationTier
    total_score: int = Field(ge=0, le=100)
    matching_level: MatchingLevel
    score_breakdown: list[ScoreBreakdown] = Field(min_length=5, max_length=5)
    matching_advantages: list[str]
    missing_skills: list[str]
    action_plan: list[str]
    alternatives: list[str]


class MajorFitReport(BaseModel):
    major: str
    matching_level: MatchingLevel
    matching_advantages: list[str]
    missing_skills: list[str]
    recommended_courses: list[str]
    recommended_projects: list[str]
    practice_tasks: list[str]


class AssessmentGuidance(BaseModel):
    top_interest_keys: list[str] = Field(default_factory=list)
    strength_evidence: list[str] = Field(default_factory=list)
    action_plan: dict[str, list[str]] = Field(default_factory=dict)
    notice: str


class CareerRecommendationResponse(BaseModel):
    profile: CareerProfile
    generated_at: str
    recommendation_notice: str
    major_report: MajorFitReport
    assessment_guidance: AssessmentGuidance | None = None
    tiers: dict[RecommendationTier, list[CareerRecommendation]]


class CareerComparisonRequest(BaseModel):
    client_id: str = Field(min_length=1, max_length=120)
    role_names: list[str] = Field(min_length=2, max_length=4)

    @field_validator("client_id")
    @classmethod
    def normalize_comparison_client_id(cls, value: str) -> str:
        return _normalize_text(value, "client_id")

    @field_validator("role_names")
    @classmethod
    def normalize_unique_role_names(cls, values: list[str]) -> list[str]:
        normalized = _normalize_list(values)
        if len(normalized) != len(values):
            raise ValueError("role_names must contain unique non-empty names")
        if len(normalized) < 2:
            raise ValueError("role_names must contain at least two roles")
        return normalized


class ComparisonActionPlan(BaseModel):
    seven_day: list[str]
    thirty_day: list[str]
    ninety_day: list[str]


class CareerComparisonItem(BaseModel):
    role: RoleProfile
    total_score: int = Field(ge=0, le=100)
    matching_level: MatchingLevel
    score_breakdown: list[ScoreBreakdown] = Field(min_length=5, max_length=5)
    matching_advantages: list[str]
    missing_skills: list[str]
    alternatives: list[str]
    risk_notice: str
    action_plan: ComparisonActionPlan


class CareerComparisonResponse(BaseModel):
    profile: CareerProfile
    items: list[CareerComparisonItem] = Field(min_length=2, max_length=4)
    common_strengths: list[str]
    recommendation_notice: str
