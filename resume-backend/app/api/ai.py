from __future__ import annotations

from fastapi import APIRouter, Request

from app.schemas.common import success
from app.schemas.job import JobQueryRequest, ResumeRewriteRequest
from app.services.rewrite_guard import validate_rewrite_facts


router = APIRouter()


@router.post("/api/job/query")
async def query_job(payload: JobQueryRequest, request: Request):
    role_name = " ".join(payload.role_name.split())
    cache = request.app.state.job_cache
    settings = request.app.state.settings
    job = cache.get(role_name, settings.ai_provider)
    if job is None:
        job = await request.app.state.ai_client.query_job(role_name)
        cache.put(role_name, settings.ai_provider, job)
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
