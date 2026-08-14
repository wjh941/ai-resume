from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.schemas.common import success
from app.services.auth import current_user_id


router = APIRouter(prefix="/api/template", tags=["templates"])


@router.get("/list")
def list_templates(request: Request, _: str = Depends(current_user_id)):
    return success(request.app.state.template_service.list_templates())
