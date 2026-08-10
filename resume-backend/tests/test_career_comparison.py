from __future__ import annotations


def assert_success(response):
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["code"] == "ok"
    return payload["data"]


def save_profile(api_client, client_id: str, skills: list[str]) -> None:
    response = api_client.post(
        "/api/career/profile/save",
        json={
            "client_id": client_id,
            "identity_code": "2",
            "major": "计算机科学与技术",
            "education_level": "本科",
            "graduation_year": 2027,
            "city_preferences": ["上海"],
            "minimum_salary": "10k",
            "industry_preferences": ["互联网"],
            "work_types": ["全职"],
            "skills": skills,
        },
    )
    assert_success(response)


def test_compare_returns_requested_roles_with_three_phase_actions(api_client):
    save_profile(api_client, client_id="compare-client", skills=["Python", "SQL"])

    data = assert_success(
        api_client.post(
            "/api/career/compare",
            json={
                "client_id": "compare-client",
                "role_names": ["数据工程师", "数据分析师"],
            },
        )
    )

    assert [item["role"]["role_name"] for item in data["items"]] == [
        "数据工程师",
        "数据分析师",
    ]
    assert all(
        set(item["action_plan"]) == {"seven_day", "thirty_day", "ninety_day"}
        for item in data["items"]
    )
    assert all("不代表录用" in item["risk_notice"] for item in data["items"])
    assert "不代表录用概率" in data["recommendation_notice"]


def test_compare_rejects_duplicate_or_out_of_range_role_names(api_client):
    save_profile(api_client, client_id="validation-client", skills=[])

    duplicate = api_client.post(
        "/api/career/compare",
        json={
            "client_id": "validation-client",
            "role_names": ["数据工程师", "数据工程师"],
        },
    )
    assert duplicate.status_code == 422

    too_many = api_client.post(
        "/api/career/compare",
        json={
            "client_id": "validation-client",
            "role_names": [
                "数据工程师",
                "数据分析师",
                "数据治理工程师",
                "机器学习工程师",
                "产品经理",
            ],
        },
    )
    assert too_many.status_code == 422
