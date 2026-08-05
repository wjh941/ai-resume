from __future__ import annotations

from fastapi import APIRouter, Request

from app.schemas.common import success


router = APIRouter(prefix="/api/template", tags=["templates"])


@router.get("/list")
def list_templates(request: Request):
    return success(request.app.state.template_service.list_templates())
