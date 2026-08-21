from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field, StrictInt, field_validator

from app.schemas.report import ReportMode


def _normalized_text(value: str, field_name: str, maximum: int) -> str:
    normalized = " ".join(value.split())
    if not normalized:
        raise ValueError(f"{field_name} must not be blank")
    if len(normalized) > maximum:
        raise ValueError(f"{field_name} is too long")
    return normalized


class AssessmentSubmitPayload(BaseModel):
    answers: dict[str, StrictInt] = Field(default_factory=dict, max_length=40)

    @field_validator("answers")
    @classmethod
    def validate_answers(cls, values: dict[str, StrictInt]) -> dict[str, int]:
        normalized: dict[str, int] = {}
        for key, value in values.items():
            normalized_key = " ".join(key.split())
            if not normalized_key or len(normalized_key) > 120:
                raise ValueError("assessment answer key is invalid")
            if not 1 <= value <= 5:
                raise ValueError("assessment answer must use the five-point scale")
            normalized[normalized_key] = int(value)
        return normalized


class AnnualInsightPayload(BaseModel):
    year: int = Field(ge=2000, le=2100)
    role_name: str = ""
    scope: str = Field(min_length=1, max_length=80)
    audience: str = Field(min_length=1, max_length=80)
    category: str = Field(min_length=1, max_length=80)
    title: str = Field(min_length=1, max_length=160)
    content: str = Field(min_length=1, max_length=3000)
    source_label: str = Field(min_length=1, max_length=200)
    publication_date: date
    confidence_note: str = Field(min_length=1, max_length=300)

    @field_validator(
        "scope",
        "audience",
        "category",
        "title",
        "content",
        "source_label",
        "confidence_note",
    )
    @classmethod
    def normalize_text_fields(cls, value: str) -> str:
        return _normalized_text(value, "text", 3000)

    @field_validator("role_name")
    @classmethod
    def normalize_role_name(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if len(normalized) > 120:
            raise ValueError("role_name is too long")
        return normalized


class AnnualInsightQueryPayload(BaseModel):
    role_name: str
    year: int | None = Field(default=None, ge=2000, le=2100)
    report_mode: ReportMode | None = None

    @field_validator("role_name")
    @classmethod
    def normalize_query_role_name(cls, value: str) -> str:
        return _normalized_text(value, "role_name", 120)
