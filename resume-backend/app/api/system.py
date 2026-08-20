from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

from app.config import Settings, load_settings
from app.db import connect
from app.schemas.common import success
from app.services.ai_client import build_ai_client
from app.services.observability import log_event


router = APIRouter(prefix="/api/system", tags=["system"])


class AIConfigPayload(BaseModel):
    """Development-only model connection form. The API key is never returned."""

    provider: Literal["ark", "openai_compatible"]
    base_url: str = Field(min_length=8, max_length=500)
    api_key: str = Field(min_length=8, max_length=1000)
    model: str = Field(min_length=1, max_length=200)

    @field_validator("base_url")
    @classmethod
    def normalize_base_url(cls, value: str) -> str:
        normalized = value.strip().rstrip("/")
        if not normalized.startswith(("https://", "http://")):
            raise ValueError("base_url must be an HTTP(S) URL")
        return normalized

    @field_validator("api_key", "model")
    @classmethod
    def normalize_secret_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("value must not be blank")
        return normalized


class ClientErrorPayload(BaseModel):
    message: str = Field(min_length=1, max_length=500)
    component: str = Field(default="", max_length=300)


def _setup_allowed(settings: Settings) -> bool:
    return settings.app_env.strip().lower() != "production" and settings.ai_config_ui_enabled


def _ai_status(settings: Settings) -> dict[str, object]:
    configured = bool(
        settings.ai_provider in {"ark", "openai_compatible"}
        and settings.ai_api_key
        and settings.ai_model
    )
    return {
        "configured": configured,
        "provider": settings.ai_provider if configured else None,
        "model": settings.ai_model if configured else None,
        "setup_allowed": _setup_allowed(settings),
        "setup_notice": (
            "Use the local development form to connect a compatible model."
            if _setup_allowed(settings)
            else "Model setup is disabled here. Configure server environment variables instead."
        ),
    }


def health_detail(settings: Settings) -> dict[str, object]:
    summary = health_summary(settings)
    return {**summary, "storage": _storage_health(settings)}


def health_summary(settings: Settings) -> dict[str, object]:
    database = _database_health(settings)
    return {
        "status": "healthy" if database["status"] == "connected" else "degraded",
        "database": database,
        "push_dispatcher_mode": settings.push_dispatcher_mode,
        "worker": _worker_health(settings),
        "backup": {
            "status": "manual",
            "hint": "Run the platform backup script and validate a restore before production deployment.",
        },
        "critical_config": {
            "production": settings.production,
            "database_url_configured": bool(settings.database_url),
            "cors_origin_count": len(settings.cors_origins),
            "sms_configured": bool(settings.sms_http_endpoint and settings.sms_access_key and settings.sms_access_secret),
            "wechat_oauth_configured": bool(settings.wechat_open_app_id and settings.wechat_open_app_secret and settings.wechat_open_redirect_uri),
            "payment_callback_configured": bool(settings.payment_callback_secret),
        },
    }


def _worker_health(settings: Settings) -> dict[str, str | None]:
    if not settings.worker_enabled:
        return {"status": "disabled", "last_completed_at": None}
    try:
        with connect(settings.database_target) as connection:
            row = connection.execute(
                "SELECT MAX(completed_at) AS completed_at FROM background_task_run"
            ).fetchone()
    except Exception:
        return {"status": "unknown", "last_completed_at": None}
    completed_at = row["completed_at"] if row else None
    if not completed_at:
        return {"status": "unknown", "last_completed_at": None}
    try:
        elapsed = datetime.now(timezone.utc) - datetime.fromisoformat(str(completed_at)).astimezone(timezone.utc)
        status = "stale" if elapsed.total_seconds() > settings.worker_scan_interval_seconds * 2 else "healthy"
    except ValueError:
        status = "unknown"
    return {"status": status, "last_completed_at": str(completed_at)}


def _database_health(settings: Settings) -> dict[str, str]:
    try:
        with connect(settings.database_target) as connection:
            connection.execute("SELECT 1").fetchone()
    except Exception:
        return {"status": "unavailable", "type": settings.database_kind}
    return {"status": "connected", "type": settings.database_kind}


def _storage_health(settings: Settings) -> dict[str, str]:
    try:
        settings.temp_file_path.mkdir(parents=True, exist_ok=True)
    except OSError:
        return {"status": "unavailable"}
    return {"status": "ready" if settings.temp_file_path.is_dir() else "unavailable"}


def _require_local_setup(request: Request) -> None:
    settings = request.app.state.settings
    if not _setup_allowed(settings):
        raise HTTPException(status_code=403, detail="Local model setup is disabled")
    host = request.client.host if request.client else ""
    if host not in {"127.0.0.1", "::1"}:
        raise HTTPException(status_code=403, detail="Local model setup only accepts loopback clients")


def _write_managed_env_values(path: Path, values: dict[str, str]) -> None:
    """Replace only AI lines, preserve existing environment comments and unrelated settings."""
    existing = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    remaining = dict(values)
    output: list[str] = []
    for line in existing:
        key, separator, _ = line.partition("=")
        if separator and key.strip() in remaining:
            output.append(f"{key.strip()}={remaining.pop(key.strip())}")
        else:
            output.append(line)
    output.extend(f"{key}={value}" for key, value in remaining.items())
    temp_path = path.with_name(f"{path.name}.tmp")
    temp_path.write_text("\n".join(output).rstrip() + "\n", encoding="utf-8")
    temp_path.replace(path)


@router.get("/ai-status")
def ai_status(request: Request) -> dict[str, object]:
    return success(_ai_status(request.app.state.settings))


@router.get("/health-detail")
def system_health_detail(request: Request) -> dict[str, object]:
    return success(health_detail(request.app.state.settings))


@router.post("/client-errors")
def report_client_error(payload: ClientErrorPayload, request: Request) -> dict[str, object]:
    log_event(
        request,
        40,
        "client_error",
        client_message=payload.message,
        component=payload.component,
    )
    return success({"recorded": True})


@router.post("/client-errors")
def report_client_error(payload: ClientErrorPayload, request: Request) -> dict[str, object]:
    log_event(
        request,
        40,
        "client_error",
        client_message=payload.message,
        component=payload.component,
    )
    return success({"recorded": True})


@router.post("/ai-config")
def configure_ai(payload: AIConfigPayload, request: Request) -> dict[str, object]:
    _require_local_setup(request)
    values = {
        "AI_PROVIDER": payload.provider,
        "AI_BASE_URL": payload.base_url,
        "AI_API_KEY": payload.api_key,
        "AI_MODEL": payload.model,
    }
    config_path = getattr(
        request.app.state,
        "ai_config_path",
        Path(__file__).resolve().parents[2] / ".env",
    )
    _write_managed_env_values(Path(config_path), values)

    # Development-only hot reload: production is blocked above and never accepts browser keys.
    os.environ.update(values)
    settings = load_settings()
    request.app.state.settings = settings
    request.app.state.ai_client = build_ai_client(settings)
    return success(_ai_status(settings))
