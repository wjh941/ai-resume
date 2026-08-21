from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


ReportMode = Literal["simplified", "professional"]


class ReportEvidence(BaseModel):
    type: str
    title: str = Field(max_length=160)
    detail: str = Field(max_length=1_000)
    date: str = Field(max_length=32)
    scope: str = Field(max_length=240)


class LayeredReport(BaseModel):
    mode: ReportMode
    summary: str = Field(max_length=1_000)
    actions: list[str] = Field(default_factory=list)
    evidence: list[ReportEvidence] = Field(default_factory=list, max_length=20)
    source_notice: str
    upgrade_notice: str

    @model_validator(mode="after")
    def limit_simplified_actions(self) -> "LayeredReport":
        if self.mode == "simplified" and len(self.actions) > 3:
            raise ValueError("simplified reports support at most three actions")
        return self
