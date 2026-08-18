from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, Path as ApiPath, Request
from fastapi.responses import FileResponse

from app.schemas.common import success
from app.schemas.exports import ExportRequest
from app.schemas.resume import ResumePayload
from app.services.export_filenames import build_export_filename
from app.services.export_pdf import PdfRendererUnavailableError, render_pdf_resume
from app.services.export_word import render_word_resume
from app.services.auth import current_user_id
from app.services.membership import VipStatus, get_current_vip


router = APIRouter(tags=["exports"])
_TOKEN_PATTERN = r"^[0-9a-f]{32}$"


class ExportEmptyError(Exception):
    pass


class ExportGenerationError(Exception):
    pass


@dataclass(frozen=True)
class ExportAccess:
    user_id: str
    vip: VipStatus


def get_export_access(
    user_id: str = Depends(current_user_id),
    vip: VipStatus = Depends(get_current_vip),
) -> ExportAccess:
    return ExportAccess(user_id=user_id, vip=vip)


@router.post("/api/export/word")
def export_word(
    payload: ExportRequest,
    request: Request,
    access: ExportAccess = Depends(get_export_access),
):
    draft = request.app.state.draft_repository.get(access.user_id, payload.draft_id)
    resume = ResumePayload.model_validate(draft["resume"])
    _ensure_exportable(resume)
    filename = build_export_filename(resume.basic.name, resume.job.target_role, "docx")
    output_path = _output_path(request, "docx")
    try:
        render_word_resume(resume, output_path, access.vip.watermark_text)
        result = request.app.state.download_service.register(access.user_id, output_path, filename)
    except OSError as error:
        _discard_partial_output(output_path)
        raise ExportGenerationError("Word export failed") from error
    return success(result.model_dump(mode="json"))


@router.post("/api/export/pdf")
async def export_pdf(
    payload: ExportRequest,
    request: Request,
    access: ExportAccess = Depends(get_export_access),
):
    draft = request.app.state.draft_repository.get(access.user_id, payload.draft_id)
    resume = ResumePayload.model_validate(draft["resume"])
    _ensure_exportable(resume)
    filename = build_export_filename(resume.basic.name, resume.job.target_role, "pdf")
    output_path = _output_path(request, "pdf")
    settings = request.app.state.settings
    try:
        await render_pdf_resume(
            resume,
            draft["template_id"],
            output_path,
            settings.pdf_renderer,
            settings.playwright_browsers_path,
            access.vip.watermark_text,
        )
        result = request.app.state.download_service.register(access.user_id, output_path, filename)
    except (OSError, PdfRendererUnavailableError) as error:
        _discard_partial_output(output_path)
        raise ExportGenerationError("PDF export failed") from error
    return success(result.model_dump(mode="json"))


@router.get("/downloads/{token}")
def download_file(
    request: Request,
    token: str = ApiPath(pattern=_TOKEN_PATTERN),
    user_id: str = Depends(current_user_id),
):
    download = request.app.state.download_service.resolve(user_id, token)
    return FileResponse(download.path, filename=download.filename)


def _output_path(request: Request, extension: str) -> Path:
    directory = request.app.state.settings.temp_file_path
    directory.mkdir(parents=True, exist_ok=True)
    return directory / f"{uuid4().hex}.{extension}"


def _ensure_exportable(resume: ResumePayload) -> None:
    visibility = resume.section_visibility
    fields = (
        [resume.basic.name, resume.basic.phone, resume.basic.email, resume.basic.city]
        if visibility.basic
        else []
    )
    if visibility.job:
        fields.append(resume.job.target_role)
    if visibility.education:
        fields.extend(
            value
            for item in resume.education
            for value in (item.school, item.major, item.degree, item.start_date, item.end_date)
        )
    if visibility.employment:
        fields.extend(
            value
            for item in resume.employment
            for value in (item.company, item.position, item.start_date, item.end_date, item.description)
        )
    if visibility.projects:
        fields.extend(
            value
            for item in resume.projects
            for value in (item.name, item.role, item.start_date, item.end_date, item.description)
        )
    if visibility.skills:
        fields.extend(resume.skills.skills + resume.skills.certificates)
    if visibility.self_evaluation:
        fields.append(resume.self_evaluation)
    if not any(value.strip() for value in fields):
        raise ExportEmptyError


def _discard_partial_output(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass
