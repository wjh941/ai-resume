from __future__ import annotations

import json
import logging

from fastapi import Request


logger = logging.getLogger("resume_api")


def configure_logging(level: str) -> None:
    logger.setLevel(getattr(logging, level, logging.INFO))


def log_event(request: Request, level: int, event: str, **context: object) -> None:
    payload = {
        "event": event,
        "request_id": getattr(request.state, "request_id", "unknown"),
        "user_id": getattr(request.state, "user_id", None),
        "method": request.method,
        "path": request.url.path,
        **context,
    }
    logger.log(
        level,
        f"{event.replace('_', ' ')} {json.dumps(payload, ensure_ascii=False, default=str, sort_keys=True)}",
    )
