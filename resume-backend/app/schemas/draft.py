from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from app.schemas.job import JobIntelligence
from app.schemas.resume import ResumePayload


class DraftSaveRequest(BaseModel):
    id: str | None = None
    client_id: str
    job_title: str
    template_id: Literal["business", "technology", "graduate", "analytics"]
    resume: ResumePayload
    job_intelligence: JobIntelligence | None = None


class DraftCopyRequest(BaseModel):
    client_id: str
