from __future__ import annotations

from fastapi import APIRouter, Query, Request

from app.schemas.career import CareerProfilePayload
from app.schemas.common import success


router = APIRouter()


@router.get("/api/role/families")
async def list_role_families(request: Request):
    items = request.app.state.career_catalog_repository.list_families()
    return success({"items": [item.model_dump() for item in items]})


@router.get("/api/role/suggestions")
async def role_suggestions(
    request: Request,
    q: str = "",
    limit: int = Query(default=12, ge=1, le=50),
):
    items = request.app.state.career_catalog_repository.search_roles(q, limit)
    return success({"items": [item.model_dump() for item in items]})


@router.get("/api/major/suggestions")
async def major_suggestions(
    request: Request,
    q: str = "",
    limit: int = Query(default=12, ge=1, le=50),
):
    items = request.app.state.career_catalog_repository.search_majors(q, limit)
    return success({"items": [item.model_dump() for item in items]})


@router.post("/api/career/profile/save")
async def save_career_profile(payload: CareerProfilePayload, request: Request):
    profile = request.app.state.career_profile_repository.save(payload)
    return success(profile.model_dump())


@router.get("/api/career/profile")
async def get_career_profile(request: Request, client_id: str):
    profile = request.app.state.career_profile_repository.get(client_id)
    return success(profile.model_dump())


@router.post("/api/career/recommend")
async def career_recommend(request: Request, client_id: str):
    profile = request.app.state.career_profile_repository.get(client_id)
    recommendation = request.app.state.career_recommender.recommend(profile)
    return success(recommendation.model_dump())
