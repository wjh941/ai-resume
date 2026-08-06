from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse

from app.schemas.common import success
from app.schemas.exports import ExportRequest
from app.schemas.resume import ResumePayload
from app.services.export_filenames import build_export_filename
from app.services.export_pdf import render_pdf_resume
from app.services.export_word import render_word_resume


router = APIRouter(tags=["exports"])


@router.post("/api/export/word")
def export_word(payload: ExportRequest, request: Request):
    draft = request.app.state.draft_repository.get(payload.draft_id, payload.client_id)
    resume = ResumePayload.model_validate(draft["resume"])
    filename = build_export_filename(resume.basic.name, resume.job.target_role, "docx")
    output_path = _output_path(request, "docx")
    render_word_resume(resume, output_path)
    result = request.app.state.download_service.register(output_path, filename)
    return success(result.model_dump(mode="json"))


@router.post("/api/export/pdf")
async def export_pdf(payload: ExportRequest, request: Request):
    draft = request.app.state.draft_repository.get(payload.draft_id, payload.client_id)
    resume = ResumePayload.model_validate(draft["resume"])
    filename = build_export_filename(resume.basic.name, resume.job.target_role, "pdf")
    output_path = _output_path(request, "pdf")
    settings = request.app.state.settings
    await render_pdf_resume(
        resume,
        draft["template_id"],
        output_path,
        settings.pdf_renderer,
        settings.playwright_browsers_path,
    )
    result = request.app.state.download_service.register(output_path, filename)
    return success(result.model_dump(mode="json"))


@router.get("/downloads/{token}")
def download_file(token: str, request: Request):
    download = request.app.state.download_service.resolve(token)
    return FileResponse(download.path, filename=download.filename)


def _output_path(request: Request, extension: str) -> Path:
    directory = request.app.state.settings.temp_file_path
    directory.mkdir(parents=True, exist_ok=True)
    return directory / f"{uuid4().hex}.{extension}"
