from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class EvidenceSuggestion(BaseModel):
    source_evidence_id: str
    source_title: str
    target_section: Literal["project", "employment"]
    title: str
    role: str
    description: str
    risk_note: str = ""


class EvidenceSuggestionResponse(BaseModel):
    items: list[EvidenceSuggestion] = Field(default_factory=list)


class ResumeReadinessReport(BaseModel):
    ready: bool
    blocking_items: list[str] = Field(default_factory=list)
    warning_items: list[str] = Field(default_factory=list)
