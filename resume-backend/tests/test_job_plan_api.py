from __future__ import annotations

import asyncio

import pytest
from pydantic import ValidationError

from conftest import grant_vip
from app.schemas.career import (
    CareerPlanComparisonItem,
    ComparisonActionPlan,
    JobPlanResponse,
    JobPlanSection,
    PromotionNode,
    PromotionTrack,
)
from test_support import TestAIClient


def make_job_plan(**changes) -> JobPlanResponse:
    payload = {
        "role_name": "Data Engineer",
        "report_scope": "brief",
        "sections": [
            JobPlanSection(key=key, title=title, summary="Summary")
            for key, title in (
                ("market_overview", "Market overview"),
                ("responsibilities", "Responsibilities"),
                ("hard_skills", "Hard skills"),
                ("soft_competencies", "Soft competencies"),
                ("career_value", "Career value"),
                ("risks", "Risks"),
            )
        ],
        "comparison_items": [
            CareerPlanComparisonItem(competency="Python", category="hard", status="high")
        ],
        "promotion_tracks": [
            PromotionTrack(
                key="technical",
                title="Technical track",
                nodes=[PromotionNode(title="Engineer", level="entry", description="Build pipelines", salary_band="10k-18k", standard_years="1-3 years", competencies=["Python"], case_detail="Build a verified project")],
            ),
            PromotionTrack(
                key="management",
                title="Management track",
                nodes=[PromotionNode(title="Lead", level="lead", description="Lead delivery", salary_band="20k-30k", standard_years="4-6 years", competencies=["Planning"], case_detail="Coordinate a delivery")],
            ),
        ],
        "action_plan": ComparisonActionPlan(seven_day=["Review"], thirty_day=["Build"], ninety_day=["Apply"]),
    }
    payload.update(changes)
    return JobPlanResponse.model_validate(payload)


def test_job_plan_requires_named_sections_and_dual_populated_tracks():
    plan = make_job_plan()
    assert {section.key for section in plan.sections} == {
        "market_overview", "responsibilities", "hard_skills", "soft_competencies", "career_value", "risks"
    }
    assert {track.key for track in plan.promotion_tracks} == {"technical", "management"}

    with pytest.raises(ValidationError):
        make_job_plan(sections=plan.sections[:-1] + [plan.sections[0]])
    with pytest.raises(ValidationError):
        make_job_plan(promotion_tracks=plan.promotion_tracks[:1])
    with pytest.raises(ValidationError):
        PromotionNode(title="Engineer", level="entry", description="Build", salary_band="", standard_years="", competencies=[], case_detail="")


def test_test_ai_client_returns_hard_and_soft_comparison_items():
    plan = asyncio.run(TestAIClient().build_job_plan("Data Engineer", {}, [], None, None, False))
    assert [item.category for item in plan.comparison_items] == ["hard", "soft"]


def test_job_plan_requires_bearer_auth(api_client):
    api_client.headers.pop("Authorization", None)
    response = api_client.post("/api/job/plan", json={"role_name": "Data Engineer"})
    assert response.status_code == 401


def _save_profile(api_client, headers, skills=None):
    response = api_client.post(
        "/api/career/profile/save",
        headers=headers,
        json={
            "identity_code": "2",
            "major": "Computer Science",
            "education_level": "Bachelor",
            "graduation_year": 2027,
            "city_preferences": ["Shanghai"],
            "minimum_salary": "10k",
            "industry_preferences": ["Internet"],
            "work_types": ["full_time"],
            "skills": skills or ["Python", "SQL"],
        },
    )
    assert response.status_code == 200, response.text


def _save_verified_evidence(api_client, headers, title):
    response = api_client.post(
        "/api/evidence",
        headers=headers,
        json={
            "kind": "project",
            "title": title,
            "context": "course project",
            "actions": "Built and verified a small data pipeline.",
            "outcome": "Documented result.",
            "proof_note": "local evidence",
            "verified": True,
        },
    )
    assert response.status_code == 200, response.text


def test_free_job_plan_ignores_expand_detail(api_client, auth_headers):
    headers = auth_headers("13900000001")
    _save_profile(api_client, headers)

    response = api_client.post(
        "/api/job/plan",
        headers=headers,
        json={"role_name": "Data Engineer", "expand_detail": True},
    )

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["report_scope"] == "brief"
    assert [track["key"] for track in data["promotion_tracks"]] == ["technical"]
    assert all(len(track["nodes"]) == 2 for track in data["promotion_tracks"])
    assert data["action_plan"]["thirty_day"] == []
    assert data["action_plan"]["ninety_day"] == []
    assert all(
        node["salary_band"] == "Details available with Basic"
        and node["standard_years"] == "Details available with Basic"
        and node["competencies"] == ["Detailed competencies available with Basic"]
        and node["case_detail"] == "Detailed roadmap available with Basic"
        and node["skills"] == []
        and node["actions"] == []
        for track in data["promotion_tracks"]
        for node in track["nodes"]
    )
    assert "10k-18k" not in response.text
    assert "Ship a verified project." not in response.text


def test_basic_job_plan_returns_detailed_content(api_client, auth_headers):
    headers = auth_headers("13900000002")
    _save_profile(api_client, headers)
    api_client.headers.update(headers)
    grant_vip(api_client, "basic")

    response = api_client.post(
        "/api/job/plan",
        headers=headers,
        json={"role_name": "Data Engineer", "expand_detail": True},
    )

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["report_scope"] == "detailed"
    assert data["action_plan"]["thirty_day"] == ["Build a Data Engineer portfolio artifact."]
    assert all(
        [node["level"] for node in track["nodes"]] == ["entry", "junior", "mid", "senior"]
        for track in data["promotion_tracks"]
    )
    assert data["promotion_tracks"][0]["nodes"][0]["salary_band"] == "10k-18k"
    assert data["promotion_tracks"][0]["nodes"][0]["case_detail"] == "Ship a verified project."


def test_basic_job_plan_can_choose_simplified_report_without_changing_detail_scope(api_client, auth_headers):
    headers = auth_headers("13900000006")
    _save_profile(api_client, headers)
    api_client.headers.update(headers)
    grant_vip(api_client, "basic")

    response = api_client.post(
        "/api/job/plan",
        headers=headers,
        json={"role_name": "Data Engineer", "expand_detail": True, "report_mode": "simplified"},
    )

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["report_scope"] == "detailed"
    assert data["report"]["mode"] == "simplified"
    assert data["report"]["evidence"] == []


def test_job_plan_never_passes_another_users_context_to_ai(api_client, auth_headers):
    owner_headers = auth_headers("13900000003")
    _save_profile(api_client, owner_headers, ["OWNER-ONLY-SKILL"])
    _save_verified_evidence(api_client, owner_headers, "OWNER-ONLY-EVIDENCE")
    other_headers = auth_headers("13900000004")

    response = api_client.post(
        "/api/job/plan",
        headers=other_headers,
        json={"role_name": "Data Engineer", "expand_detail": False},
    )

    assert response.status_code == 200, response.text
    context = api_client.app.state.ai_client.last_job_plan_context
    assert context["profile"] == {}
    assert context["evidence"] == []


def test_job_plan_accepts_missing_optional_user_records(api_client, auth_headers):
    headers = auth_headers("13900000005")

    response = api_client.post(
        "/api/job/plan",
        headers=headers,
        json={"role_name": "Data Engineer", "expand_detail": False},
    )

    assert response.status_code == 200, response.text
    context = api_client.app.state.ai_client.last_job_plan_context
    assert context["profile"] == {}
    assert context["resume"] is None
    assert context["assessment"] is None
