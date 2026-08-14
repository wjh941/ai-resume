from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request

from app.schemas.assessment import AnnualInsightPayload, AssessmentSubmitPayload
from app.schemas.common import success
from app.services.career_assessment import assessment_questions
from app.services.auth import current_user_id


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
    return success(saved)


@router.get("/api/career/assessment")
async def get_assessment(request: Request, user_id: str = Depends(current_user_id)) -> dict[str, object]:
    return success(request.app.state.assessment_repository.get(user_id))


@router.post("/api/career/annual-insights")
async def create_annual_insight(
    payload: AnnualInsightPayload,
    request: Request,
    _: str = Depends(current_user_id),
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
) -> dict[str, object]:
    return success(
        {"items": request.app.state.assessment_repository.list_annual_insights(year)}
    )
