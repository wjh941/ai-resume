from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.config import Settings
from app.repositories.drafts import DraftRepository
from app.repositories.resume_imports import ResumeImportRecord, ResumeImportRepository
from app.services.resume_parser import ResumeParseError, parse_resume_file


class ResumeImportValidationError(ValueError):
    pass


_ALLOWED_UPLOADS = {
    ".pdf": "application/pdf",
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
        self._expire_minutes = settings.resume_import_expire_minutes

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
            raise ResumeImportValidationError("仅支持 PDF 和 DOCX 格式的简历文件。")

        import_id = uuid4().hex
        self._directory.mkdir(parents=True, exist_ok=True)
        destination = self._directory / f"{import_id}{suffix}"
        written = 0
        try:
            with destination.open("xb") as target:
                while chunk := await upload.read(64 * 1024):
                    written += len(chunk)
                    if written > self._max_file_bytes:
                        raise ResumeImportValidationError("简历文件超过当前允许的大小限制。")
                    target.write(chunk)
            _validate_file_signature(destination, suffix)
            try:
                parsed = parse_resume_file(destination, suffix)
            except ResumeParseError as error:
                raise ResumeImportValidationError(str(error)) from error
            return self._imports.create(
                import_id,
                user_id,
                draft_id,
                destination.name,
                original_filename,
                expected_content_type,
                written,
                parsed.resume,
            )
        except Exception:
            destination.unlink(missing_ok=True)
            raise
        finally:
            await upload.close()

    def cleanup_expired(self, now: datetime | None = None) -> int:
        current = now or datetime.now(timezone.utc)
        cutoff = current - timedelta(minutes=self._expire_minutes)
        expired = self._imports.list_expired(cutoff)
        for _, stored_filename in expired:
            candidate = (self._directory / stored_filename).resolve()
            try:
                candidate.relative_to(self._directory.resolve())
            except ValueError:
                continue
            candidate.unlink(missing_ok=True)
        return self._imports.delete_many([import_id for import_id, _ in expired])


def _validate_file_signature(path: Path, suffix: str) -> None:
    with path.open("rb") as source:
        signature = source.read(8)
    expected = b"%PDF-" if suffix == ".pdf" else b"PK\x03\x04"
    if not signature.startswith(expected):
        raise ResumeImportValidationError("简历文件格式无效，请上传真实的 PDF 或 DOCX 文件。")
