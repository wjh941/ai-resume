from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.schemas.common import success
from app.schemas.knowledgebase import OperatorKnowledgeCreate, OperatorKnowledgeUpdate
from app.services.auth import AuthPrincipal, require_operator


router = APIRouter(prefix="/api/operator", tags=["operator"])


@router.get("/knowledge-items")
def list_knowledge_items(request: Request, _: AuthPrincipal = Depends(require_operator)):
    return success({"items": request.app.state.operator_knowledge_repository.list_items()})


@router.post("/knowledge-items")
def create_knowledge_item(
    payload: OperatorKnowledgeCreate,
    request: Request,
    principal: AuthPrincipal = Depends(require_operator),
):
    return success(request.app.state.operator_knowledge_repository.create(principal.user_id, payload))


@router.patch("/knowledge-items/{item_id}")
def update_knowledge_item(
    item_id: str,
    payload: OperatorKnowledgeUpdate,
    request: Request,
    principal: AuthPrincipal = Depends(require_operator),
):
    return success(request.app.state.operator_knowledge_repository.update(principal.user_id, item_id, payload))


@router.get("/knowledge-items/{item_id}/versions")
def list_knowledge_versions(item_id: str, request: Request, _: AuthPrincipal = Depends(require_operator)):
    return success({"items": request.app.state.operator_knowledge_repository.list_versions(item_id)})


@router.post("/knowledge-items/{item_id}/versions/{version}/restore")
def restore_knowledge_version(
    item_id: str,
    version: int,
    request: Request,
    principal: AuthPrincipal = Depends(require_operator),
):
    return success(
        request.app.state.operator_knowledge_repository.restore_version(principal.user_id, item_id, version)
    )
