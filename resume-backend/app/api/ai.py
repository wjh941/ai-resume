from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.repositories.assessment import AssessmentNotFoundError
from app.repositories.career_profiles import CareerProfileNotFoundError
from app.schemas.career import JobMatchRequest, JobMatchResponse
from app.schemas.common import success
from app.schemas.job import JobQueryRequest, ResumeRewriteRequest
from app.services.auth import current_user_id
from app.services.job_matching import MatchContext
from app.services.rewrite_guard import validate_rewrite_facts
from app.services.membership import VipPermissionError, VipStatus, get_current_vip
from app.services.report_tiering import make_report_evidence, project_report


router = APIRouter()


def _match_context(request: Request, user_id: str, target_role: str) -> MatchContext:
    skills: list[str] = []
    target_roles = [target_role] if target_role else []
    try:
        profile = request.app.state.career_profile_repository.get(user_id)
        skills.extend(profile.skills)
        target_roles.extend(profile.industry_preferences)
    except CareerProfileNotFoundError:
        pass

    drafts = request.app.state.draft_repository.list(user_id)
    if drafts:
        resume = drafts[0]["resume"]
        skills.extend(resume.get("skills", {}).get("skills", []))
        target = str(resume.get("job", {}).get("target_role", ""))
        if target:
            target_roles.append(target)

    evidence = request.app.state.evidence_repository.list(user_id)
    evidence_text = " ".join(
        " ".join([item.title, item.context, item.actions, item.outcome])
        for item in evidence
    )
    try:
        assessment = request.app.state.assessment_repository.get(user_id)["result"]
        target_roles.extend(str(item) for item in assessment.get("recommended_roles", []))
    except AssessmentNotFoundError:
        pass
    return MatchContext(skills=skills, evidence_text=evidence_text, target_roles=target_roles)


@router.get("/api/job/suggestions")
async def query_job_suggestions(request: Request, q: str = ""):
    items = request.app.state.job_catalog.search(q)
    return success({"items": [item.model_dump() for item in items]})


@router.get("/api/job/market-search")
async def search_job_market(request: Request, role_name: str):
    normalized_role = " ".join(role_name.split())
    report = await request.app.state.web_search_client.search(
        f"{normalized_role} 招聘要求 薪资 职业发展"
    )
    return success(report.model_dump())


@router.post("/api/job/query")
async def query_job(
    payload: JobQueryRequest,
    request: Request,
    vip: VipStatus = Depends(get_current_vip),
):
    role_name = " ".join(payload.role_name.split())
    cache = request.app.state.job_cache
    settings = request.app.state.settings
    provider_cache_key = settings.ai_provider
    job = cache.get(role_name, provider_cache_key)
    if job is None:
        job = await request.app.state.ai_client.query_job(role_name)
        cache.put(role_name, provider_cache_key, job)
    job_payload = job.model_dump()
    focus_items = [*job.required_skills, *job.hard_requirements, *job.responsibilities]
    report = project_report(
        payload.report_mode,
        "simplified",
        vip,
        "full_job_report",
        f"{job.role_name}的岗位要点用于求职准备，不代表实时招聘信息。",
        [f"围绕{item}准备一项可展示的成果" for item in focus_items[:3]],
        [
            make_report_evidence(
                "analysis_framework",
                f"结构化岗位要点：{item}",
                "来自本地结构化岗位知识，用于准备和复核正式 JD。",
                scope=job.role_name,
            )
            for item in focus_items[:20]
        ],
        "资料范围：本地结构化岗位知识，不包含实时岗位数量或薪资数据。",
        [*job.responsibilities, *job.career_route],
    )
    job_payload["report"] = report.model_dump(mode="json")
    return success(job_payload)


@router.post("/api/job/match")
async def match_jobs(
    payload: JobMatchRequest,
    request: Request,
    user_id: str = Depends(current_user_id),
    vip: VipStatus = Depends(get_current_vip),
):
    # Candidate context is built from the JWT owner only; request bodies contain filters, never identity.
    context = _match_context(request, user_id, payload.target_role)
    items = request.app.state.job_matcher.match(
        context,
        request.app.state.career_catalog_repository.list_roles(),
        payload,
        detail_unlocked=vip.vip_level in {"basic", "premium"},
    )
    limited = vip.vip_level == "free" and len(items) > 3
    response = JobMatchResponse(
        items=items[:3] if vip.vip_level == "free" else items,
        total=len(items),
        limited=limited,
        source_notice=(
            "匹配基于当前登录账号的简历、经历、测评和本地岗位目录，不是实时招聘职位；"
            "公司、城市和薪资仅供方向筛选，请以正式 JD 核验。"
        ),
    )
    verified_evidence = [
        item
        for item in request.app.state.evidence_repository.list(user_id)
        if item.verified
    ]
    missing_skills = [skill for item in items for skill in item.missing_skills]
    response_payload = response.model_dump()
    response_payload["report"] = project_report(
        payload.report_mode,
        "professional" if vip.allows("full_job_report") else "simplified",
        vip,
        "full_job_report",
        "岗位匹配基于当前账户的资料和本地岗位目录，不代表实时招聘结果。",
        [f"补充 {skill} 的可验证项目或经历" for skill in missing_skills[:3]]
        or ["完善一项与目标岗位相关的已验证经历"],
        [
            make_report_evidence(
                "personal_evidence",
                item.title,
                f"{item.context} {item.actions} {item.outcome}",
                scope=payload.target_role or "岗位匹配",
            )
            for item in verified_evidence[:20]
        ],
        "资料范围：当前账户已验证经历与本地岗位目录，不包含实时招聘信息。",
        [
            f"将已验证经历映射到 {item.role_name} 的职责和技能要求"
            for item in items[:3]
        ],
    ).model_dump(mode="json")
    return success(response_payload)


@router.post("/api/resume/ai-rewrite")
async def rewrite_resume(
    payload: ResumeRewriteRequest,
    request: Request,
    vip: VipStatus = Depends(get_current_vip),
):
    if payload.mode == "deep" and vip.vip_level == "free":
        raise VipPermissionError("深度 AI 润色需要基础会员或高级会员")
    rewritten = await request.app.state.ai_client.rewrite_resume(
        payload.resume,
        payload.job,
        payload.mode,
    )
    validate_rewrite_facts(payload.resume, rewritten)
    rewritten_payload = rewritten.model_dump()
    resume_items = [
        *( (item.name, item.role, item.description) for item in payload.resume.projects ),
        *( (item.company, item.position, item.description) for item in payload.resume.employment ),
    ]
    rewritten_payload["report"] = project_report(
        payload.report_mode,
        "professional" if payload.mode == "deep" and vip.allows("full_job_report") else "simplified",
        vip,
        "full_job_report",
        f"简历润色围绕 {payload.job.role_name} 的岗位关键词组织表达，事实仍以原始简历为准。",
        [
            "核对润色内容是否与原始经历一致",
            "补充一项可验证的项目交付物",
            "使用正式 JD 复核关键词与职责对应关系",
        ],
        [
            make_report_evidence(
                "analysis_framework",
                title,
                f"{role} {description}",
                scope=payload.job.role_name,
            )
            for title, role, description in resume_items[:20]
            if title or description
        ],
        "资料范围：本次提交的简历和岗位信息；不生成或补充未经验证的事实。",
        [
            f"逐条核对简历内容与 {payload.job.role_name} 的职责匹配关系",
            "为关键项目准备可复核的交付物或证明材料",
            "根据真实面试反馈迭代一版简历",
        ],
    ).model_dump(mode="json")
    return success(rewritten_payload)
