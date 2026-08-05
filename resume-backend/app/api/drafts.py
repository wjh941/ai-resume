from __future__ import annotations

from fastapi import APIRouter, Request

from app.repositories.drafts import DraftNotFoundError
from app.schemas.common import success
from app.schemas.draft import DraftCopyRequest, DraftSaveRequest


router = APIRouter(prefix="/api/draft", tags=["drafts"])


@router.post("/save")
def save_draft(payload: DraftSaveRequest, request: Request):
    return success(request.app.state.draft_repository.save(payload))


@router.get("/list")
def list_drafts(client_id: str, request: Request):
    return success(request.app.state.draft_repository.list(client_id))


@router.get("/{draft_id}")
def get_draft(draft_id: str, client_id: str, request: Request):
    return success(request.app.state.draft_repository.get(draft_id, client_id))


@router.post("/{draft_id}/copy")
def copy_draft(draft_id: str, payload: DraftCopyRequest, request: Request):
    return success(request.app.state.draft_repository.copy(draft_id, payload.client_id))


@router.delete("/{draft_id}")
def delete_draft(draft_id: str, client_id: str, request: Request):
    request.app.state.draft_repository.delete(draft_id, client_id)
    return success({"id": draft_id})
