from __future__ import annotations

from app.services.membership import VipStatus
from app.services.report_tiering import ReportEvidenceInput, project_report


EVIDENCE = [
    ReportEvidenceInput(
        type="personal_evidence",
        title="Private SQL migration",
        detail="Migrated reporting queries to SQL.",
        date="2026-08",
        scope="Data engineering portfolio",
    ),
]


def test_free_professional_request_returns_simplified_without_evidence():
    report = project_report(
        requested_mode="professional",
        default_mode="simplified",
        vip=VipStatus("free", None, False),
        required_feature="full_job_report",
        summary="Build a focused SQL portfolio.",
        actions=["Practice joins", "Publish one project", "Review metrics", "Hidden fourth action"],
        evidence=EVIDENCE,
        source_notice="Source data is illustrative.",
        professional_actions=["Map evidence to requirements"],
    )

    assert report.mode == "simplified"
    assert report.evidence == []
    assert report.actions == ["Practice joins", "Publish one project", "Review metrics"]
    assert report.upgrade_notice
    assert "Private SQL migration" not in report.model_dump_json()


def test_basic_user_can_choose_simplified_or_professional():
    vip = VipStatus("basic", None, False)

    assert project_report(
        "simplified", "professional", vip, "full_job_report", "Summary", ["Action"], [], "Source", ["Professional action"]
    ).mode == "simplified"
    assert project_report(
        "professional", "simplified", vip, "full_job_report", "Summary", ["Action"], EVIDENCE, "Source", ["Professional action"]
    ).mode == "professional"


def test_missing_mode_uses_adapter_default_without_changing_legacy_behavior():
    report = project_report(
        None,
        "professional",
        VipStatus("basic", None, False),
        "full_job_report",
        "Summary",
        ["Action"],
        [],
        "Source",
        ["Professional action"],
    )

    assert report.mode == "professional"


def test_anonymous_default_professional_never_grants_evidence():
    report = project_report(
        None, "professional", None, "full_job_report", "Summary", ["Action"], EVIDENCE, "Source", ["Professional action"]
    )

    assert report.mode == "simplified"
    assert report.evidence == []
    assert "Private SQL migration" not in report.model_dump_json()




def test_job_query_adds_a_simplified_report_without_changing_job_fields(api_client):
    response = api_client.post("/api/job/query", json={"role_name": "Data Analyst"})

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["role_name"] == "Data Analyst"
    assert data["report"]["mode"] == "simplified"
    assert data["report"]["evidence"] == []
