from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.repositories.assessment import AssessmentNotFoundError
from app.schemas.career import CareerComparisonRequest, CareerProfilePayload, ComparisonActionPlan
from app.schemas.common import success
from app.services.auth import current_user_id
from app.services.membership import VipPermissionError, VipStatus, get_current_vip


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
async def career_recommend(
    request: Request,
    user_id: str = Depends(current_user_id),
    vip: VipStatus = Depends(get_current_vip),
):
    profile = request.app.state.career_profile_repository.get(user_id)
    try:
        assessment = request.app.state.assessment_repository.get(user_id)
    except AssessmentNotFoundError:
        assessment = None
    assessment_result = assessment["result"] if assessment else None
    if assessment_result and not vip.allows("full_assessment"):
        # 同一份已存档测评不能经推荐接口绕过 Free 版的 7/30/90 天路线限制。
        assessment_result = {**assessment_result, "action_plan": {}}
    recommendation = request.app.state.career_recommender.recommend(
        profile,
        assessment_result=assessment_result,
    )
    return success(recommendation.model_dump())


@router.post("/api/career/compare")
async def career_compare(
    payload: CareerComparisonRequest,
    request: Request,
    user_id: str = Depends(current_user_id),
    vip: VipStatus = Depends(get_current_vip),
):
    if len(payload.role_names) > vip.max_compare_jobs:
        raise VipPermissionError(
            f"当前会员最多对比 {vip.max_compare_jobs} 个岗位，请升级后继续分析"
        )
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
    for item in comparison.items:
        if vip.vip_level == "free":
            # Free 保留当周行动建议；完整 7/30/90 天路线由基础会员以上解锁。
            item.action_plan = ComparisonActionPlan(
                seven_day=[f"核对 {item.role.role_name} 的两项核心技能，并补充一条真实经历。"],
                thirty_day=[],
                ninety_day=[],
            )
        else:
            item.action_plan = await request.app.state.ai_client.build_comparison_action_plan(
                item.role.role_name,
                profile.model_dump(),
                [entry.title for entry in evidence if entry.verified],
            )
    return success(comparison.model_dump())
