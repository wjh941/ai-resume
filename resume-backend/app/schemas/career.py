from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.consultation import IdentityCode


MatchingLevel = Literal["high", "transferable", "needs_upskilling", "long_shot"]
RecommendationTier = Literal["stretch", "stable", "safe"]
JobPlanSectionKey = Literal[
    "market_overview",
    "responsibilities",
    "hard_skills",
    "soft_competencies",
    "career_value",
    "risks",
]
PromotionTrackKey = Literal["technical", "management"]


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

    @field_validator("major", "education_level")
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
    role_names: list[str] = Field(min_length=2, max_length=4)

    @field_validator("role_names")
    @classmethod
    def normalize_unique_role_names(cls, values: list[str]) -> list[str]:
        normalized = _normalize_list(values)
        if len(normalized) != len(values):
            raise ValueError("role_names must contain unique non-empty names")
        if len(normalized) < 2:
            raise ValueError("role_names must contain at least two roles")
        return normalized


class JobMatchRequest(BaseModel):
    """Filters only. Candidate data is derived from JWT-owned repositories."""

    city: str = Field(default="", max_length=80)
    salary_min: int | None = Field(default=None, ge=0, le=500)
    salary_max: int | None = Field(default=None, ge=0, le=500)
    seniority: Literal["", "entry", "mid", "senior"] = ""
    category: str = Field(default="", max_length=80)
    target_role: str = Field(default="", max_length=120)

    @field_validator("city", "category", "target_role")
    @classmethod
    def normalize_filter_text(cls, value: str) -> str:
        return " ".join(value.split())


class JobMatchItem(BaseModel):
    role_name: str
    company: str
    city: str
    salary_range: str
    seniority: Literal["entry", "mid", "senior"]
    category: str
    match_score: int = Field(ge=0, le=100)
    matched_skills: list[str]
    missing_skills: list[str]
    description: str
    responsibilities: list[str]
    requirements: list[str]
    match_score_reference: int | None = Field(default=None, ge=0, le=100)
    detail_unlocked: bool


class JobMatchResponse(BaseModel):
    items: list[JobMatchItem]
    total: int = Field(ge=0)
    limited: bool
    source_notice: str


class ComparisonActionPlan(BaseModel):
    seven_day: list[str]
    thirty_day: list[str]
    ninety_day: list[str]


CareerTaskStatus = Literal["pending", "completed"]


class CareerTaskSaveRequest(BaseModel):
    id: str | None = Field(default=None, max_length=120)
    plan_id: str = Field(min_length=1, max_length=120)
    title: str = Field(min_length=1, max_length=240)
    description: str = Field(default="", max_length=4_000)
    due_date: date | None = None
    status: CareerTaskStatus = "pending"
    link_to_application_id: str | None = Field(default=None, max_length=120)
    link_to_evidence_id: str | None = Field(default=None, max_length=120)

    @field_validator("plan_id", "title")
    @classmethod
    def normalize_required_task_text(cls, value: str) -> str:
        return _normalize_text(value, "task text")

    @field_validator("description", "link_to_application_id", "link_to_evidence_id")
    @classmethod
    def normalize_optional_task_text(cls, value: str | None) -> str | None:
        return " ".join(value.split()) if value is not None else None


class CareerTaskUpdateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=240)
    description: str | None = Field(default=None, max_length=4_000)
    due_date: date | None = None
    status: CareerTaskStatus | None = None
    link_to_application_id: str | None = Field(default=None, max_length=120)
    link_to_evidence_id: str | None = Field(default=None, max_length=120)


class CareerTaskRecord(CareerTaskSaveRequest):
    id: str
    created_at: str
    updated_at: str


class CareerTaskGenerateRequest(BaseModel):
    plan_id: str = Field(min_length=1, max_length=120)
    action_plan: ComparisonActionPlan


class JobPlanRequest(BaseModel):
    role_name: str = Field(min_length=1, max_length=120)
    expand_detail: bool = False

    @field_validator("role_name")
    @classmethod
    def normalize_role_name(cls, value: str) -> str:
        return _normalize_text(value, "role_name")


class JobPlanSection(BaseModel):
    key: JobPlanSectionKey
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    items: list[str] = Field(default_factory=list)


class CareerPlanComparisonItem(BaseModel):
    competency: str
    category: Literal["hard", "soft"]
    status: MatchingLevel
    evidence: list[str] = Field(default_factory=list)
    gap: str = ""
    recommendation: str = ""


class PromotionNode(BaseModel):
    title: str = Field(min_length=1)
    level: str = Field(min_length=1)
    description: str = Field(min_length=1)
    salary_band: str = Field(min_length=1)
    standard_years: str = Field(min_length=1)
    competencies: list[str] = Field(min_length=1)
    case_detail: str = Field(min_length=1)
    skills: list[str] = Field(default_factory=list)
    actions: list[str] = Field(default_factory=list)


class PromotionTrack(BaseModel):
    key: PromotionTrackKey
    title: str = Field(min_length=1)
    nodes: list[PromotionNode] = Field(min_length=1)


class JobPlanResponse(BaseModel):
    role_name: str
    report_scope: Literal["brief", "detailed"]
    sections: list[JobPlanSection] = Field(min_length=6, max_length=6)
    comparison_items: list[CareerPlanComparisonItem]
    promotion_tracks: list[PromotionTrack]
    action_plan: ComparisonActionPlan

    @field_validator("sections")
    @classmethod
    def require_named_sections(cls, sections: list[JobPlanSection]) -> list[JobPlanSection]:
        required = {"market_overview", "responsibilities", "hard_skills", "soft_competencies", "career_value", "risks"}
        if {section.key for section in sections} != required:
            raise ValueError("sections must contain each required job-plan section exactly once")
        return sections

    @field_validator("promotion_tracks")
    @classmethod
    def require_dual_promotion_tracks(cls, tracks: list[PromotionTrack]) -> list[PromotionTrack]:
        if len(tracks) != 2 or {track.key for track in tracks} != {"technical", "management"}:
            raise ValueError("promotion_tracks must contain technical and management tracks")
        return tracks

    @model_validator(mode="after")
    def require_detailed_roadmap_stages(self) -> "JobPlanResponse":
        """Keep the paid roadmap visually complete and deterministic for the dashboard."""
        if self.report_scope != "detailed":
            return self
        expected_levels = ["entry", "junior", "mid", "senior"]
        if any(
            [node.level for node in track.nodes] != expected_levels
            for track in self.promotion_tracks
        ):
            raise ValueError(
                "detailed promotion tracks must contain entry, junior, mid, senior nodes"
            )
        return self


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
