from __future__ import annotations

from fastapi import APIRouter, Query, Request

from app.schemas.application import ApplicationSaveRequest, ApplicationStatus
from app.schemas.common import success


router = APIRouter(prefix="/api/applications", tags=["applications"])


@router.get("")
def list_applications(
    request: Request,
    client_id: str,
    status: ApplicationStatus | None = Query(default=None),
):
    items = request.app.state.application_repository.list(client_id, status)
    return success({"items": [item.model_dump(mode="json") for item in items]})


@router.post("")
def save_application(payload: ApplicationSaveRequest, request: Request):
    application = request.app.state.application_repository.save(payload)
    return success(application.model_dump(mode="json"))


@router.delete("/{application_id}")
def delete_application(application_id: str, client_id: str, request: Request):
    request.app.state.application_repository.delete(application_id, client_id)
    return success({"id": application_id})
