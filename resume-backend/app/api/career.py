from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.repositories.assessment import AssessmentNotFoundError
from app.schemas.career import CareerComparisonRequest, CareerProfilePayload
from app.schemas.common import success
from app.services.auth import current_user_id


router = APIRouter()


@router.get("/api/role/families")
async def list_role_families(request: Request, _: str = Depends(current_user_id)):
    items = request.app.state.career_catalog_repository.list_families()
    return success({"items": [item.model_dump() for item in items]})


@router.get("/api/role/suggestions")
async def role_suggestions(
    request: Request,
    q: str = "",
    limit: int = Query(default=12, ge=1, le=50),
    _: str = Depends(current_user_id),
):
    items = request.app.state.career_catalog_repository.search_roles(q, limit)
    return success({"items": [item.model_dump() for item in items]})


@router.get("/api/major/suggestions")
async def major_suggestions(
    request: Request,
    q: str = "",
    limit: int = Query(default=12, ge=1, le=50),
    _: str = Depends(current_user_id),
):
    items = request.app.state.career_catalog_repository.search_majors(q, limit)
    return success({"items": [item.model_dump() for item in items]})


@router.post("/api/career/profile/save")
async def save_career_profile(
    payload: CareerProfilePayload,
    request: Request,
    user_id: str = Depends(current_user_id),
):
    profile = request.app.state.career_profile_repository.save(user_id, payload)
    return success(profile.model_dump())


@router.get("/api/career/profile")
async def get_career_profile(request: Request, user_id: str = Depends(current_user_id)):
    profile = request.app.state.career_profile_repository.get(user_id)
    return success(profile.model_dump())


@router.post("/api/career/recommend")
async def career_recommend(request: Request, user_id: str = Depends(current_user_id)):
    profile = request.app.state.career_profile_repository.get(user_id)
    try:
        assessment = request.app.state.assessment_repository.get(user_id)
    except AssessmentNotFoundError:
        assessment = None
    recommendation = request.app.state.career_recommender.recommend(
        profile,
        assessment_result=assessment["result"] if assessment else None,
    )
    return success(recommendation.model_dump())


@router.post("/api/career/compare")
async def career_compare(
    payload: CareerComparisonRequest,
    request: Request,
    user_id: str = Depends(current_user_id),
):
    profile = request.app.state.career_profile_repository.get(user_id)
    try:
        roles = request.app.state.career_catalog_repository.get_roles_by_names(
            payload.role_names
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    evidence = request.app.state.evidence_repository.list(user_id)
    comparison = request.app.state.career_recommender.compare(
        profile,
        roles,
        verified_evidence=[item for item in evidence if item.verified],
    )
    return success(comparison.model_dump())
