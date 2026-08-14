from __future__ import annotations

from conftest import grant_vip

def test_role_comparison_uses_ai_for_each_seven_thirty_ninety_plan(api_client):
    grant_vip(api_client)
    profile = {
        "identity_code": "2",
        "major": "Computer Science",
        "education_level": "Bachelor",
        "skills": ["Python", "SQL"],
    }
    assert api_client.post("/api/career/profile/save", json=profile).status_code == 200

    response = api_client.post(
        "/api/career/compare",
        json={"role_names": ["数据工程师", "数据分析师"]},
    )

    assert response.status_code == 200
    assert api_client.app.state.ai_client.action_plan_query_count == 2
