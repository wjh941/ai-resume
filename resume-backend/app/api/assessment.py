from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request

from app.schemas.assessment import AnnualInsightPayload, AssessmentSubmitPayload
from app.schemas.common import success
from app.services.career_assessment import assessment_questions
from app.services.auth import current_user_id
from app.services.membership import VipStatus, get_current_vip, require_vip_feature


router = APIRouter()


@router.get("/api/career/assessment/questions")
async def get_assessment_questions(_: str = Depends(current_user_id)) -> dict[str, object]:
    return success(
        {
            "items": assessment_questions(),
            "notice": "本测评用于职业决策支持，不是心理或医疗诊断，也不承诺就业结果。",
        }
    )


@router.post("/api/career/assessment/submit")
async def submit_assessment(
    payload: AssessmentSubmitPayload,
    request: Request,
    user_id: str = Depends(current_user_id),
    vip: VipStatus = Depends(get_current_vip),
) -> dict[str, object]:
    result = await request.app.state.ai_client.assess_career(
        assessment_questions(), payload.answers
    )
    saved = request.app.state.assessment_repository.save(
        user_id,
        version=1,
        answers=payload.answers,
        result=result,
    )
    return success(_assessment_for_vip(saved, vip))


@router.get("/api/career/assessment")
async def get_assessment(
    request: Request,
    user_id: str = Depends(current_user_id),
    vip: VipStatus = Depends(get_current_vip),
) -> dict[str, object]:
    return success(_assessment_for_vip(request.app.state.assessment_repository.get(user_id), vip))


@router.post("/api/career/annual-insights")
async def create_annual_insight(
    payload: AnnualInsightPayload,
    request: Request,
    _: str = Depends(current_user_id),
    __: VipStatus = Depends(require_vip_feature("industry_insight")),
) -> dict[str, object]:
    created = request.app.state.assessment_repository.save_annual_insight(
        payload.model_dump(mode="json")
    )
    return success(created)


@router.get("/api/career/annual-insights")
async def list_annual_insights(
    request: Request,
    year: int | None = Query(default=None, ge=2000, le=2100),
    _: str = Depends(current_user_id),
    __: VipStatus = Depends(require_vip_feature("industry_insight")),
) -> dict[str, object]:
    return success(
        {"items": request.app.state.assessment_repository.list_annual_insights(year)}
    )


def _assessment_for_vip(saved: dict[str, object], vip: VipStatus) -> dict[str, object]:
    """Free 保留基础测评结论，不向本地缓存暴露完整长期职业路线。"""
    if vip.allows("full_assessment"):
        return saved
    result = dict(saved.get("result", {}))
    result.pop("action_plan", None)
    result["report_scope"] = "simplified"
    result["upgrade_notice"] = "升级基础会员可解锁完整 7/30/90 天职业路线。"
    return {**saved, "result": result}
