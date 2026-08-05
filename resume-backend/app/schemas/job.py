from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class JobIntelligence(BaseModel):
    version: Literal[1] = 1
    role_name: str
    salary_by_experience: dict[str, str] = Field(default_factory=dict)
    responsibilities: list[str] = Field(default_factory=list)
    hard_requirements: list[str] = Field(default_factory=list)
    required_skills: list[str] = Field(default_factory=list)
    bonus_skills: list[str] = Field(default_factory=list)
    career_route: list[str] = Field(default_factory=list)
