from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


def _normalize(value: str, maximum: int, required: bool = False) -> str:
    normalized = " ".join(value.split())
    if required and not normalized:
        raise ValueError("text must not be blank")
    if len(normalized) > maximum:
        raise ValueError("text is too long")
    return normalized


class FavoriteJobCreate(BaseModel):
    role_name: str = Field(min_length=1, max_length=160)
    note: str = Field(default="", max_length=1_000)

    @field_validator("role_name")
    @classmethod
    def normalize_role_name(cls, value: str) -> str:
        return _normalize(value, 160, required=True)

    @field_validator("note")
    @classmethod
    def normalize_note(cls, value: str) -> str:
        return _normalize(value, 1_000)


class JobSubscriptionUpdate(BaseModel):
    enabled: bool
    match_filter: str | None = Field(default=None, max_length=200)

    @field_validator("match_filter")
    @classmethod
    def normalize_match_filter(cls, value: str | None) -> str | None:
        return _normalize(value, 200) if value is not None else None
