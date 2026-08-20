from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.config import Settings
from app.repositories.drafts import DraftRepository
from app.repositories.resume_imports import ResumeImportRecord, ResumeImportRepository


class ResumeImportValidationError(ValueError):
    pass


_ALLOWED_UPLOADS = {
    ".pdf": "application/pdf",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def empty_resume_preview() -> dict[str, object]:
    return {
        "version": 1,
        "basic": {"name": "", "phone": "", "email": "", "city": ""},
        "job": {"target_role": "", "employment_type": "", "expected_salary": ""},
        "education": [],
        "employment": [],
        "projects": [],
        "skills": {"skills": [], "certificates": []},
        "self_evaluation": "",
        "section_visibility": {
            "basic": True,
            "job": True,
            "education": True,
            "employment": True,
            "projects": True,
            "skills": True,
            "self_evaluation": True,
        },
    }


class ResumeImportService:
    def __init__(
        self,
        settings: Settings,
        drafts: DraftRepository,
        imports: ResumeImportRepository,
    ) -> None:
        self._drafts = drafts
        self._imports = imports
        self._directory = settings.temp_file_path / "resume-imports"
        self._max_file_bytes = settings.resume_import_max_file_bytes

    async def accept_upload(
        self,
        user_id: str,
        draft_id: str,
        upload: UploadFile,
    ) -> ResumeImportRecord:
        self._drafts.get(user_id, draft_id)
        original_filename = Path(upload.filename or "").name
        suffix = Path(original_filename).suffix.lower()
        expected_content_type = _ALLOWED_UPLOADS.get(suffix)
        if not expected_content_type or upload.content_type != expected_content_type:
            raise ResumeImportValidationError("Only PDF, DOC, and DOCX resume files are accepted.")

        import_id = uuid4().hex
        self._directory.mkdir(parents=True, exist_ok=True)
        destination = self._directory / f"{import_id}{suffix}"
        written = 0
        try:
            with destination.open("xb") as target:
                while chunk := await upload.read(64 * 1024):
                    written += len(chunk)
                    if written > self._max_file_bytes:
                        raise ResumeImportValidationError("The resume file exceeds the configured size limit.")
                    target.write(chunk)
            # TODO: Malware scanning and PDF/Word parsing are deferred until provider integration is approved.
            return self._imports.create(
                import_id,
                user_id,
                draft_id,
                destination.name,
                original_filename,
                expected_content_type,
                written,
                empty_resume_preview(),
            )
        except Exception:
            destination.unlink(missing_ok=True)
            raise
        finally:
            await upload.close()
