from __future__ import annotations

from fastapi import APIRouter, Depends

from app.schemas.common import success
from app.services.auth import current_user_id


router = APIRouter(prefix="/api/account", tags=["account"])


@router.get("/data-scope")
def data_scope(_: str = Depends(current_user_id)):
    return success({
        "categories": ["resume_drafts", "career_profiles", "applications", "account_identity", "membership_orders"],
        "retention_note": "Account lifecycle actions are acknowledgement-only in this development phase.",
    })


@router.post("/deletion-request")
def request_deletion(_: str = Depends(current_user_id)):
    # TODO: Add verified identity checks and a recoverable retention workflow before deleting any data.
    return success({"status": "requested", "message": "No account data has been deleted."})


@router.post("/data-export")
def request_data_export(_: str = Depends(current_user_id)):
    # TODO: Build an asynchronous, access-controlled archive once export retention and storage are approved.
    return success({"status": "not_started", "message": "Data export is not generated in this development phase."})
