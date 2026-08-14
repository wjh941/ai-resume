from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.repositories.drafts import DraftNotFoundError
from app.schemas.common import success
from app.schemas.draft import DraftCopyRequest, DraftSaveRequest
from app.services.auth import current_user_id


router = APIRouter(prefix="/api/draft", tags=["drafts"])


@router.post("/save")
def save_draft(payload: DraftSaveRequest, request: Request, user_id: str = Depends(current_user_id)):
    return success(request.app.state.draft_repository.save(user_id, payload))


@router.get("/list")
def list_drafts(request: Request, user_id: str = Depends(current_user_id)):
    return success(request.app.state.draft_repository.list(user_id))


@router.get("/{draft_id}")
def get_draft(draft_id: str, request: Request, user_id: str = Depends(current_user_id)):
    return success(request.app.state.draft_repository.get(user_id, draft_id))


@router.post("/{draft_id}/copy")
def copy_draft(
    draft_id: str,
    _: DraftCopyRequest,
    request: Request,
    user_id: str = Depends(current_user_id),
):
    return success(request.app.state.draft_repository.copy(user_id, draft_id))


@router.delete("/{draft_id}")
def delete_draft(draft_id: str, request: Request, user_id: str = Depends(current_user_id)):
    request.app.state.draft_repository.delete(user_id, draft_id)
    return success({"id": draft_id})
