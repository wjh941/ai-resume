from __future__ import annotations

from io import BytesIO

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from pypdf import PdfReader

from app.schemas.common import success
from app.schemas.consultation import AdviceRequest, JobConsultationRequest, ResumeReviewRequest
from app.services.membership import VipStatus, require_vip_feature
from app.services.rate_limit import enforce_ai_rate_limit


router = APIRouter()


@router.post("/api/consultation/job-analysis")
async def job_analysis(
    payload: JobConsultationRequest,
    request: Request,
    _: VipStatus = Depends(require_vip_feature("full_job_report")),
    _rate_limit: None = Depends(enforce_ai_rate_limit),
):
    job = await _get_job_intelligence(payload.role_name, request)
    result = await request.app.state.ai_client.build_job_consultation(
        job,
        payload.identity_code,
        payload.custom_requirement,
    )
    return success(result.model_dump())


@router.post("/api/consultation/resume-review")
async def resume_review(
    payload: ResumeReviewRequest,
    request: Request,
    _rate_limit: None = Depends(enforce_ai_rate_limit),
):
    result = await request.app.state.ai_client.review_resume_text(
        payload.resume_text,
        payload.identity_code,
        payload.role_name,
        payload.custom_requirement,
    )
    return success(result.model_dump())


@router.post("/api/consultation/advice")
async def career_advice(
    payload: AdviceRequest,
    request: Request,
    _rate_limit: None = Depends(enforce_ai_rate_limit),
):
    result = await request.app.state.ai_client.build_career_advice(
        payload.identity_code,
        payload.topic,
        payload.role_name,
        payload.question,
    )
    return success(result.model_dump())


@router.post("/api/consultation/resume-pdf-extract")
async def extract_resume_pdf(file: UploadFile = File(...)):
    filename = (file.filename or "").casefold()
    if file.content_type != "application/pdf" and not filename.endswith(".pdf"):
        raise HTTPException(status_code=422, detail="仅支持 PDF 格式的文件")
    content = await file.read()
    if not content or len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=422, detail="PDF 文件大小需在 10 MB 以内")
    try:
        reader = PdfReader(BytesIO(content))
        text = "\n".join(page.extract_text() or "" for page in reader.pages).strip()
    except Exception as error:
        raise HTTPException(status_code=422, detail="无法解析该 PDF 的内容") from error
    if not text:
        raise HTTPException(status_code=422, detail="该 PDF 中没有可提取的文字，可能是扫描件")
    return success({"text": text})


async def _get_job_intelligence(role_name: str, request: Request):
    normalized_role = " ".join(role_name.split())
    cache = request.app.state.job_cache
    settings = request.app.state.settings
    provider_cache_key = settings.ai_provider
    job = cache.get(normalized_role, provider_cache_key)
    if job is None:
        job = await request.app.state.ai_client.query_job(normalized_role)
        cache.put(normalized_role, provider_cache_key, job)
    return job
