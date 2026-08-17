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
async def query_job(payload: JobQueryRequest, request: Request):
    role_name = " ".join(payload.role_name.split())
    cache = request.app.state.job_cache
    settings = request.app.state.settings
    provider_cache_key = settings.ai_provider
    job = cache.get(role_name, provider_cache_key)
    if job is None:
        job = await request.app.state.ai_client.query_job(role_name)
        cache.put(role_name, provider_cache_key, job)
    return success(job.model_dump())


@router.post("/api/job/match")
async def match_jobs(
    payload: JobMatchRequest,
    request: Request,
    user_id: str = Depends(current_user_id),
    vip: VipStatus = Depends(get_current_vip),
):
    # Candidate context is built from the JWT owner only; request bodies contain filters, never identity.
    items = request.app.state.job_matcher.match(
        _match_context(request, user_id, payload.target_role),
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
    return success(response.model_dump())


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
    return success(rewritten.model_dump())
