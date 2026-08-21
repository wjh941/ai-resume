from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request

from app.schemas.assessment import (
    AnnualInsightPayload,
    AnnualInsightQueryPayload,
    AssessmentSubmitPayload,
)
from app.schemas.common import success
from app.schemas.report import ReportMode
from app.services.report_tiering import (
    ReportEvidenceInput,
    make_report_evidence,
    project_report,
)
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
    return success(_assessment_with_report(saved, vip, payload.report_mode))


@router.get("/api/career/assessment")
async def get_assessment(
    request: Request,
    user_id: str = Depends(current_user_id),
    vip: VipStatus = Depends(get_current_vip),
    report_mode: ReportMode | None = Query(default=None),
) -> dict[str, object]:
    return success(
        _assessment_with_report(
            request.app.state.assessment_repository.get(user_id),
            vip,
            report_mode,
        )
    )


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


@router.post("/api/career/annual-insights/query")
async def query_annual_insights(
    payload: AnnualInsightQueryPayload,
    request: Request,
    vip: VipStatus = Depends(get_current_vip),
) -> dict[str, object]:
    items = request.app.state.assessment_repository.list_annual_insights_for_role(
        payload.role_name,
        payload.year,
    )
    source_notice = "资料范围：仅使用已归档年度资料，不包含实时招聘信息。"
    concise_actions = [
        "核验目标岗位职责与交付物",
        "补充一项与岗位对应的已验证经历",
        "结合正式 JD 复核后安排下一步行动",
    ]
    if items:
        summary = (
            f"已找到与{payload.role_name}相关的{len(items)}条归档年度资料，"
            "可用于组织求职准备，不代表实时岗位供给或录用结果。"
        )
        evidence = [
            ReportEvidenceInput(
                type="annual_source",
                title=str(item["title"]),
                detail=_annual_evidence_detail(item),
                date=str(item["publication_date"]),
                scope=str(item["scope"]),
            )
            for item in items
        ]
        professional_actions = [
            f"阅读《{item['title']}》并整理{item['category']}相关的准备要点"
            for item in items[:3]
        ]
    else:
        summary = "暂无可核验年度资料，可先参考岗位基础能力并补充已验证经历。"
        evidence = []
        professional_actions = concise_actions

    report = project_report(
        payload.report_mode,
        "simplified",
        vip,
        "industry_insight",
        summary,
        concise_actions,
        evidence,
        source_notice,
        professional_actions,
    )
    return success(
        {
            "role_name": payload.role_name,
            "year": payload.year,
            "report": report.model_dump(mode="json"),
        }
    )


def _annual_evidence_detail(item: dict[str, object]) -> str:
    source_label = str(item["source_label"])
    content = str(item["content"])
    confidence_note = str(item["confidence_note"])
    prefix = f"来源：{source_label}。"
    suffix = f" 置信说明：{confidence_note}"
    content_limit = 1_000 - len(prefix) - len(suffix)
    if len(content) > content_limit:
        content = f"{content[:content_limit - 3]}..."
    return f"{prefix}{content}{suffix}"


def _assessment_with_report(
    saved: dict[str, object],
    vip: VipStatus,
    report_mode: ReportMode | None,
) -> dict[str, object]:
    projected = _assessment_for_vip(saved, vip)
    result = dict(saved.get("result", {}))
    top_interests = result.get("top_interests", [])
    strength_evidence = result.get("strength_evidence", [])
    action_plan = result.get("action_plan", {})
    concise_actions = list(action_plan.get("seven_day", []))[:3] or [
        "选择一个目标岗位并核验职责",
        "补充一项可验证的项目或经历",
        "根据真实反馈更新求职准备",
    ]
    professional_actions = [
        *list(action_plan.get("seven_day", [])),
        *list(action_plan.get("thirty_day", [])),
        *list(action_plan.get("ninety_day", [])),
    ]
    report = project_report(
        report_mode,
        "professional" if vip.allows("full_assessment") else "simplified",
        vip,
        "full_assessment",
        "职业测评用于整理当前偏好与答题信息，不是心理诊断或就业结果承诺。",
        concise_actions,
        [
            make_report_evidence(
                "analysis_framework",
                str(item.get("label", item.get("key", "兴趣方向"))),
                f"{item.get('reason', '')} 得分：{item.get('score', '')}",
                scope="职业测评",
            )
            for item in top_interests[:3]
            if isinstance(item, dict)
        ]
        + [
            make_report_evidence(
                "analysis_framework",
                "答题中的能力线索",
                strength,
                scope="职业测评",
            )
            for strength in strength_evidence[:17]
        ],
        "资料范围：当前账户提交的测评答案和本地测评规则。",
        professional_actions or concise_actions,
    )
    return {**projected, "report": report.model_dump(mode="json")}


def _assessment_for_vip(saved: dict[str, object], vip: VipStatus) -> dict[str, object]:
    """Free 保留基础测评结论，不向本地缓存暴露完整长期职业路线。"""
    if vip.allows("full_assessment"):
        return saved
    result = dict(saved.get("result", {}))
    result.pop("action_plan", None)
    result["report_scope"] = "simplified"
    result["upgrade_notice"] = "升级基础会员可解锁完整 7/30/90 天职业路线。"
    return {**saved, "result": result}
