from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.repositories.assessment import AssessmentNotFoundError
from app.repositories.career_profiles import CareerProfileNotFoundError
from app.repositories.drafts import DraftNotFoundError
from app.schemas.career import (
    CareerComparisonRequest,
    CareerProfilePayload,
    CareerTaskGenerateRequest,
    CareerTaskSaveRequest,
    CareerTaskUpdateRequest,
    ComparisonActionPlan,
    JobPlanRequest,
    JobPlanResponse,
)
from app.schemas.common import success
from app.services.auth import current_user_id
from app.services.membership import VipPermissionError, VipStatus, get_current_vip
from app.services.report_tiering import make_report_evidence, project_report


router = APIRouter()


def _job_plan_context(request: Request, user_id: str) -> tuple[dict[str, object], list[dict[str, object]], dict[str, object] | None, dict[str, object] | None]:
    """Assemble the plan context from JWT-owned repositories only."""
    try:
        profile_model = request.app.state.career_profile_repository.get(user_id)
        profile = profile_model.model_dump()
    except CareerProfileNotFoundError:
        profile = {}

    evidence = [
        item.model_dump()
        for item in request.app.state.evidence_repository.list(user_id)
        if item.verified
    ]

    draft = None
    draft_id = profile.get("draft_id")
    if draft_id:
        try:
            draft = request.app.state.draft_repository.get(user_id, str(draft_id))
        except DraftNotFoundError:
            draft = None
    if draft is None:
        drafts = request.app.state.draft_repository.list(user_id)
        draft = drafts[0] if drafts else None

    try:
        assessment = request.app.state.assessment_repository.get(user_id)["result"]
    except AssessmentNotFoundError:
        assessment = None
    return profile, evidence, draft["resume"] if draft else None, assessment


def project_job_plan_for_vip(plan: JobPlanResponse, vip: VipStatus) -> JobPlanResponse:
    """The browser can request detail, but entitlement projection stays server authoritative."""
    if vip.allows("full_job_report"):
        return plan
    technical_track = next(track for track in plan.promotion_tracks if track.key == "technical")
    return plan.model_copy(
        update={
            "report_scope": "brief",
            "sections": [section.model_copy(update={"items": section.items[:1]}) for section in plan.sections],
            "comparison_items": [
                item.model_copy(update={"evidence": item.evidence[:1], "gap": "", "recommendation": ""})
                for item in plan.comparison_items[:2]
            ],
            # Free receives only a technical preview. Management progression is paid-only.
            "promotion_tracks": [
                technical_track.model_copy(
                    update={
                        "nodes": [
                            node.model_copy(
                                update={
                                    "description": "Preview the current career stage and unlock detailed requirements with Basic.",
                                    "salary_band": "Details available with Basic",
                                    "standard_years": "Details available with Basic",
                                    "competencies": ["Detailed competencies available with Basic"],
                                    "case_detail": "Detailed roadmap available with Basic",
                                    "skills": [],
                                    "actions": [],
                                }
                            )
                            for node in technical_track.nodes[:2]
                        ]
                    }
                )
            ],
            "action_plan": ComparisonActionPlan(
                seven_day=plan.action_plan.seven_day[:1],
                thirty_day=[],
                ninety_day=[],
            ),
        }
    )


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


@router.get("/api/career/tasks")
async def list_career_tasks(
    request: Request,
    plan_id: str = Query(min_length=1, max_length=120),
    user_id: str = Depends(current_user_id),
):
    items = request.app.state.career_task_repository.list(user_id, plan_id)
    return success({"items": [item.model_dump(mode="json") for item in items]})


@router.post("/api/career/tasks")
async def save_career_task(
    payload: CareerTaskSaveRequest,
    request: Request,
    user_id: str = Depends(current_user_id),
):
    task = request.app.state.career_task_repository.save(user_id, payload)
    return success(task.model_dump(mode="json"))


@router.patch("/api/career/tasks/{task_id}")
async def update_career_task(
    task_id: str,
    payload: CareerTaskUpdateRequest,
    request: Request,
    user_id: str = Depends(current_user_id),
):
    task = request.app.state.career_task_repository.update(user_id, task_id, payload)
    return success(task.model_dump(mode="json"))


@router.delete("/api/career/tasks/{task_id}")
async def delete_career_task(
    task_id: str,
    request: Request,
    user_id: str = Depends(current_user_id),
):
    request.app.state.career_task_repository.delete(user_id, task_id)
    return success({"id": task_id})


@router.post("/api/career/tasks/generate")
async def generate_career_tasks(
    payload: CareerTaskGenerateRequest,
    request: Request,
    user_id: str = Depends(current_user_id),
):
    items = request.app.state.career_task_repository.generate_from_action_plan(
        user_id, payload.plan_id, payload.action_plan
    )
    return success({"items": [item.model_dump(mode="json") for item in items]})


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


@router.post("/api/job/plan")
async def job_plan(
    payload: JobPlanRequest,
    request: Request,
    user_id: str = Depends(current_user_id),
    vip: VipStatus = Depends(get_current_vip),
):
    profile, evidence, resume, assessment = _job_plan_context(request, user_id)
    expand_detail = payload.expand_detail and vip.allows("full_job_report")
    plan = await request.app.state.ai_client.build_job_plan(
        payload.role_name,
        profile,
        evidence,
        resume,
        assessment,
        expand_detail,
    )
    projected_plan = project_job_plan_for_vip(plan, vip)
    plan_payload = projected_plan.model_dump()
    concise_actions = projected_plan.action_plan.seven_day[:3] or [
        "核验目标岗位的职责和交付物",
        "补充一项可验证的项目或经历",
        "使用正式 JD 复核下一步行动",
    ]
    professional_actions = [
        *projected_plan.action_plan.seven_day,
        *projected_plan.action_plan.thirty_day,
        *projected_plan.action_plan.ninety_day,
    ]
    plan_payload["report"] = project_report(
        payload.report_mode,
        "professional" if projected_plan.report_scope == "detailed" else "simplified",
        vip,
        "full_job_report",
        f"{payload.role_name}的职业规划基于当前账户资料和本地规则生成，应以正式 JD 和真实反馈复核。",
        concise_actions,
        [
            make_report_evidence(
                "personal_evidence",
                item.get("title", "已验证经历"),
                f"{item.get('context', '')} {item.get('actions', '')} {item.get('outcome', '')}",
                scope=payload.role_name,
            )
            for item in evidence[:20]
        ],
        "资料范围：当前账户已验证经历、简历和本地职业规划规则。",
        professional_actions or concise_actions,
    ).model_dump(mode="json")
    return success(plan_payload)
