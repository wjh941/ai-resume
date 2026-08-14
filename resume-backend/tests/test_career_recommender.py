from __future__ import annotations

from conftest import grant_vip


def assert_success(response):
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["code"] == "ok"
    return payload["data"]


def test_career_recommendation_has_non_overlapping_stretch_stable_safe_tiers(api_client):
    profile = {
        "client_id": "recommend-client",
        "identity_code": "2",
        "major": "计算机科学与技术",
        "education_level": "本科",
        "graduation_year": 2027,
        "city_preferences": ["上海"],
        "minimum_salary": "10k",
        "industry_preferences": ["互联网"],
        "work_types": ["全职"],
        "skills": ["Python", "SQL"],
    }
    assert_success(api_client.post("/api/career/profile/save", json=profile))

    data = assert_success(
        api_client.post("/api/career/recommend", params={"client_id": "recommend-client"})
    )
    tiers = data["tiers"]
    all_items = [item for tier in ("stretch", "stable", "safe") for item in tiers[tier]]
    role_names = [item["role"]["role_name"] for item in all_items]

    assert set(tiers) == {"stretch", "stable", "safe"}
    assert all(tiers[tier] for tier in tiers)
    assert len(role_names) == len(set(role_names))
    stable_families = {item["role"]["family"] for item in tiers["stable"]}
    assert "数据与数据平台" in stable_families
    assert len(stable_families) >= 3
    assert all(len(item["score_breakdown"]) == 5 for item in all_items)
    assert "不代表录用概率" in data["recommendation_notice"]


def test_career_recommendation_adds_guidance_only_after_assessment(api_client):
    profile = {
        "client_id": "assessment-recommend-client",
        "identity_code": "2",
        "major": "Computer Science",
        "education_level": "Bachelor",
        "skills": ["Python", "SQL"],
    }
    assert_success(api_client.post("/api/career/profile/save", json=profile))
    grant_vip(api_client, "basic")
    assert_success(
        api_client.post(
            "/api/career/assessment/submit",
            json={
                "client_id": "assessment-recommend-client",
                "answers": {
                    "interest_investigative_1": 5,
                    "evidence_sql_1": 4,
                    "style_structure_1": 5,
                },
            },
        )
    )

    data = assert_success(
        api_client.post(
            "/api/career/recommend",
            params={"client_id": "assessment-recommend-client"},
        )
    )

    assert data["assessment_guidance"]["top_interest_keys"] == ["investigative"]
    assert data["assessment_guidance"]["strength_evidence"]
    assert data["assessment_guidance"]["action_plan"]["thirty_day"]
