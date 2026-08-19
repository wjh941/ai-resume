from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from app.schemas.common import success
from app.services.auth import current_user_id


router = APIRouter(prefix="/api/account", tags=["account"])


@router.get("/data-scope")
def data_scope(_: str = Depends(current_user_id)):
    return success({
        "categories": ["resume_drafts", "career_profiles", "applications", "account_identity", "membership_orders"],
        "retention_note": "Deletion anonymizes resume and career data while retaining required order audit records.",
        "privacy_policy_hint": "Export your data before deletion. Deleted accounts cannot sign in again.",
    })


@router.post("/deletion-request")
def request_deletion(request: Request, user_id: str = Depends(current_user_id)):
    request.app.state.account_privacy_repository.soft_delete(user_id)
    return success({"status": "deleted", "message": "Account has been soft-deleted and personal resume data anonymized."})


@router.post("/data-export")
def request_data_export(_: str = Depends(current_user_id)):
    return success({"status": "ready", "message": "Your data export is ready.", "download_url": "/api/account/data-export"})


@router.get("/data-export")
def download_data_export(request: Request, user_id: str = Depends(current_user_id)):
    archive = request.app.state.account_privacy_repository.export_archive(user_id)
    return StreamingResponse(
        iter([archive]),
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=ai-resume-account-data.zip"},
    )


@router.post("/privacy-consent")
def record_privacy_consent(request: Request, user_id: str = Depends(current_user_id)):
    consent_at = request.app.state.account_privacy_repository.record_privacy_consent(user_id)
    return success({"privacy_consent_at": consent_at})
