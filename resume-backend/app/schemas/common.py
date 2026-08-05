from __future__ import annotations

from typing import Any


def success(data: Any) -> dict[str, Any]:
    return {"code": "ok", "data": data, "message": ""}


def error(code: str, message: str) -> dict[str, Any]:
    return {"code": code, "data": {}, "message": message}
