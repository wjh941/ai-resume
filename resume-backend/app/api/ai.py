from __future__ import annotations

from fastapi import APIRouter, Request

from app.schemas.common import success
from app.schemas.job import JobQueryRequest, ResumeRewriteRequest
from app.services.rewrite_guard import validate_rewrite_facts


router = APIRouter()


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


@router.post("/api/resume/ai-rewrite")
async def rewrite_resume(payload: ResumeRewriteRequest, request: Request):
    rewritten = await request.app.state.ai_client.rewrite_resume(
        payload.resume,
        payload.job,
        payload.mode,
    )
    validate_rewrite_facts(payload.resume, rewritten)
    return success(rewritten.model_dump())
