from __future__ import annotations

from pathlib import Path

import pytest

from app.repositories.applications import ApplicationNotFoundError
from app.repositories.drafts import DraftNotFoundError
from app.repositories.assessment import AssessmentNotFoundError
from app.repositories.career_profiles import CareerProfileNotFoundError
from app.repositories.users import UserRecord
from app.services.downloads import DownloadNotFoundError
from app.schemas.application import ApplicationSaveRequest
from app.schemas.career import CareerProfilePayload
from app.schemas.evidence import ResumeEvidenceSaveRequest
from app.schemas.draft import DraftSaveRequest

from conftest import make_draft_payload


def _two_users(api_client) -> tuple[UserRecord, UserRecord]:
    users = api_client.app.state.user_repository
    return (
        users.find_or_create_by_phone("13800138000"),
        users.find_or_create_by_phone("13900139000"),
    )


def test_draft_and_evidence_queries_are_bound_to_the_repository_user(api_client):
    owner, other = _two_users(api_client)
    draft_repository = api_client.app.state.draft_repository
    evidence_repository = api_client.app.state.evidence_repository

    draft = draft_repository.save(
        owner.user_id,
        DraftSaveRequest.model_validate(make_draft_payload()),
    )
    evidence = evidence_repository.save(
        owner.user_id,
        ResumeEvidenceSaveRequest(
            client_id="forged-client-id",
            kind="project",
            title="Data Platform",
            actions="Built data quality checks.",
        ),
    )

    with pytest.raises(DraftNotFoundError):
        draft_repository.get(other.user_id, draft["id"])
    assert evidence_repository.list(other.user_id) == []
    assert evidence_repository.delete(other.user_id, evidence.id) is False


def test_application_and_profile_queries_are_bound_to_the_repository_user(api_client):
    owner, other = _two_users(api_client)
    applications = api_client.app.state.application_repository
    profiles = api_client.app.state.career_profile_repository

    application = applications.save(
        owner.user_id,
        ApplicationSaveRequest(
            client_id="forged-client-id",
            company="Example Company",
            role_name="Data Engineer",
        ),
    )
    profile = profiles.save(
        owner.user_id,
        CareerProfilePayload(
            client_id="forged-client-id",
            identity_code="1",
            major="Computer Science",
            education_level="Bachelor",
        ),
    )

    with pytest.raises(ApplicationNotFoundError):
        applications.delete(other.user_id, application.id)
    with pytest.raises(CareerProfileNotFoundError):
        profiles.get(other.user_id)
    assert profiles.get(owner.user_id).major == profile.major


def test_assessment_and_download_records_are_bound_to_the_repository_user(api_client, tmp_path):
    owner, other = _two_users(api_client)
    assessments = api_client.app.state.assessment_repository
    downloads = api_client.app.state.download_service

    assessment = assessments.save(
        owner.user_id,
        version=1,
        answers={"interest": 5},
        result={"recommended_roles": ["Data Engineer"]},
    )
    output_path = Path(tmp_path) / "resume.docx"
    output_path.write_text("resume", encoding="utf-8")
    download = downloads.register(owner.user_id, output_path, "resume.docx")

    with pytest.raises(AssessmentNotFoundError):
        assessments.get(other.user_id)
    assert assessment["answers"] == {"interest": 5}
    with pytest.raises(DownloadNotFoundError):
        downloads.resolve(other.user_id, download.download_url.rsplit("/", 1)[-1])
