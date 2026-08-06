from __future__ import annotations

import re

from app.schemas.exports import ExportExtension


_INVALID_FILENAME_CHARACTERS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_WHITESPACE = re.compile(r"\s+")


def _safe_filename_part(value: str, fallback: str) -> str:
    normalized = _INVALID_FILENAME_CHARACTERS.sub("-", value).strip(" .-")
    normalized = _WHITESPACE.sub(" ", normalized)
    return normalized or fallback


def build_export_filename(name: str, role: str, extension: ExportExtension) -> str:
    safe_name = _safe_filename_part(name, "未命名")
    safe_role = _safe_filename_part(role, "目标岗位")
    return f"{safe_name}-{safe_role}-简历.{extension}"
