from __future__ import annotations

from fastapi import APIRouter, Request

from app.repositories.knowledgebase import KnowledgebaseRoleNotFoundError
from app.schemas.common import success
from app.schemas.knowledgebase import KnowledgebaseRoleInput


router = APIRouter()


@router.post("/api/knowledgebase/roles")
async def create_role(payload: KnowledgebaseRoleInput, request: Request):
    role = request.app.state.knowledgebase_repository.create_manual_role(payload)
    return success(role.model_dump())


@router.get("/api/knowledgebase/roles/{role_name}")
async def get_role(role_name: str, request: Request):
    role = request.app.state.knowledgebase_repository.get_role(role_name)
    return success(role.model_dump())


@router.post("/api/knowledgebase/sync/official")
async def sync_official_dataset(request: Request):
    summary = await request.app.state.official_dataset_sync_service.sync()
    return success(summary.model_dump())


@router.get("/api/knowledgebase/sources")
async def list_sources(request: Request):
    items = request.app.state.knowledgebase_repository.list_sources()
    return success({"items": [item.model_dump() for item in items]})