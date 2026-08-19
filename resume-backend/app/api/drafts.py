from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.repositories.drafts import DraftLimitReachedError, DraftNotFoundError
from app.schemas.common import success
from app.schemas.draft import DraftCopyRequest, DraftSaveRequest, DraftVersionCreateRequest
from app.services.auth import current_user_id
from app.services.membership import VipPermissionError, VipStatus, get_current_vip


router = APIRouter(prefix="/api/draft", tags=["drafts"])


@router.post("/save")
def save_draft(
    payload: DraftSaveRequest,
    request: Request,
    user_id: str = Depends(current_user_id),
    vip: VipStatus = Depends(get_current_vip),
):
    try:
        return success(request.app.state.draft_repository.save(user_id, payload, vip.max_drafts))
    except DraftLimitReachedError as error:
        raise VipPermissionError("Free 会员最多保存 3 份简历草稿，请升级后继续新增") from error


@router.get("/list")
def list_drafts(request: Request, user_id: str = Depends(current_user_id)):
    return success(request.app.state.draft_repository.list(user_id))


@router.get("/{draft_id}/versions")
def list_versions(draft_id: str, request: Request, user_id: str = Depends(current_user_id)):
    return success({"items": request.app.state.draft_repository.list_versions(user_id, draft_id)})


@router.post("/{draft_id}/versions")
def create_version(
    draft_id: str,
    payload: DraftVersionCreateRequest,
    request: Request,
    user_id: str = Depends(current_user_id),
):
    return success(request.app.state.draft_repository.create_version(user_id, draft_id, payload.note))


@router.get("/{draft_id}/versions/compare")
def compare_versions(
    draft_id: str,
    request: Request,
    left_id: str = Query(min_length=1, max_length=120),
    right_id: str = Query(min_length=1, max_length=120),
    user_id: str = Depends(current_user_id),
):
    return success(
        request.app.state.draft_repository.compare_versions(user_id, draft_id, left_id, right_id)
    )


@router.post("/{draft_id}/versions/{version_id}/restore")
def restore_version(
    draft_id: str,
    version_id: str,
    request: Request,
    user_id: str = Depends(current_user_id),
):
    return success(request.app.state.draft_repository.restore_version(user_id, draft_id, version_id))


@router.post("/{draft_id}/import")
def import_resume_document(draft_id: str):
    raise HTTPException(
        status_code=501,
        detail="文档解析将在后续版本提供，请先手动补充简历内容。",
    )


@router.get("/{draft_id}")
def get_draft(draft_id: str, request: Request, user_id: str = Depends(current_user_id)):
    return success(request.app.state.draft_repository.get(user_id, draft_id))


@router.post("/{draft_id}/copy")
def copy_draft(
    draft_id: str,
    _: DraftCopyRequest,
    request: Request,
    user_id: str = Depends(current_user_id),
    vip: VipStatus = Depends(get_current_vip),
):
    try:
        return success(request.app.state.draft_repository.copy(user_id, draft_id, vip.max_drafts))
    except DraftLimitReachedError as error:
        raise VipPermissionError("Free 会员最多保存 3 份简历草稿，请升级后继续新增") from error


@router.delete("/{draft_id}")
def delete_draft(draft_id: str, request: Request, user_id: str = Depends(current_user_id)):
    request.app.state.draft_repository.delete(user_id, draft_id)
    return success({"id": draft_id})
