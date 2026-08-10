from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.schemas.common import error, success
from app.schemas.evidence import ResumeEvidenceSaveRequest
from app.schemas.resume_quality import (
    EvidenceSuggestionRequest,
    EvidenceSuggestionResponse,
    ResumeReadinessRequest,
)
from app.services.evidence_suggestions import build_evidence_suggestions
from app.services.resume_readiness import inspect_resume_readiness


router = APIRouter(tags=["evidence"])


@router.get("/api/evidence")
def list_evidence(client_id: str, request: Request):
    items = request.app.state.evidence_repository.list(client_id)
    return success({"items": [item.model_dump() for item in items]})


@router.post("/api/evidence")
def save_evidence(payload: ResumeEvidenceSaveRequest, request: Request):
    try:
        saved = request.app.state.evidence_repository.save(payload)
    except KeyError:
        return _not_found()
    return success(saved.model_dump())


@router.delete("/api/evidence/{evidence_id}")
def delete_evidence(evidence_id: str, client_id: str, request: Request):
    deleted = request.app.state.evidence_repository.delete(evidence_id, client_id)
    if not deleted:
        return _not_found()
    return success({"id": evidence_id})


@router.post("/api/resume/evidence-suggestions")
def evidence_suggestions(payload: EvidenceSuggestionRequest, request: Request):
    evidence_items = request.app.state.evidence_repository.list(payload.client_id)
    items = build_evidence_suggestions(payload.role_name, evidence_items)
    return success(EvidenceSuggestionResponse(items=items).model_dump())


@router.post("/api/resume/readiness")
def resume_readiness(payload: ResumeReadinessRequest):
    report = inspect_resume_readiness(payload.resume)
    return success(report.model_dump())


def _not_found() -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content=error("not_found", "Evidence not found"),
    )
