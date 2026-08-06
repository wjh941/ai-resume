from __future__ import annotations

from fastapi import APIRouter, Request

from app.schemas.common import success
from app.schemas.consultation import JobConsultationRequest, ResumeReviewRequest
from app.services.ai_client import MOCK_CACHE_KEY


router = APIRouter()


@router.post("/api/consultation/job-analysis")
async def job_analysis(payload: JobConsultationRequest, request: Request):
    job = await _get_job_intelligence(payload.role_name, request)
    result = await request.app.state.ai_client.build_job_consultation(job, payload.identity_code)
    return success(result.model_dump())


@router.post("/api/consultation/resume-review")
async def resume_review(payload: ResumeReviewRequest, request: Request):
    result = await request.app.state.ai_client.review_resume_text(
        payload.resume_text,
        payload.identity_code,
        payload.role_name,
    )
    return success(result.model_dump())


async def _get_job_intelligence(role_name: str, request: Request):
    normalized_role = " ".join(role_name.split())
    cache = request.app.state.job_cache
    settings = request.app.state.settings
    provider_cache_key = MOCK_CACHE_KEY if settings.ai_provider == "mock" else settings.ai_provider
    job = cache.get(normalized_role, provider_cache_key)
    if job is None:
        job = await request.app.state.ai_client.query_job(normalized_role)
        cache.put(normalized_role, provider_cache_key, job)
    return job
