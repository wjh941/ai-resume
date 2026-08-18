from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ExportRequest(BaseModel):
    draft_id: str = Field(
        min_length=32,
        max_length=36,
        pattern=r"^[0-9a-fA-F-]+$",
    )


class ExportResult(BaseModel):
    filename: str
    download_url: str
    expires_at: datetime


ExportExtension = Literal["docx", "pdf"]
