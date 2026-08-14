from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request

from app.schemas.application import ApplicationSaveRequest, ApplicationStatus
from app.schemas.common import success
from app.services.auth import current_user_id


router = APIRouter(prefix="/api/applications", tags=["applications"])


@router.get("")
def list_applications(
    request: Request,
    status: ApplicationStatus | None = Query(default=None),
    user_id: str = Depends(current_user_id),
):
    items = request.app.state.application_repository.list(user_id, status)
    return success({"items": [item.model_dump(mode="json") for item in items]})


@router.post("")
def save_application(
    payload: ApplicationSaveRequest,
    request: Request,
    user_id: str = Depends(current_user_id),
):
    application = request.app.state.application_repository.save(user_id, payload)
    return success(application.model_dump(mode="json"))


@router.delete("/{application_id}")
def delete_application(
    application_id: str,
    request: Request,
    user_id: str = Depends(current_user_id),
):
    request.app.state.application_repository.delete(user_id, application_id)
    return success({"id": application_id})
