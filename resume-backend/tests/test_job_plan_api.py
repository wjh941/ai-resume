from __future__ import annotations

import asyncio

import pytest
from pydantic import ValidationError

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
