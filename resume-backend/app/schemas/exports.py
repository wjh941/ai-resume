from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class ExportRequest(BaseModel):
    client_id: str
    draft_id: str


class ExportResult(BaseModel):
    filename: str
    download_url: str
    expires_at: datetime


ExportExtension = Literal["docx", "pdf"]
