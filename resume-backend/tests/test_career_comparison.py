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


def test_compare_uses_only_verified_existing_skill_evidence(api_client):
    save_profile(api_client, client_id="evidence-client", skills=[])
    for payload in (
        {
            "client_id": "evidence-client",
            "kind": "project",
            "title": "Python 数据处理课程项目",
            "context": "课程练习",
            "actions": "使用 Python 清洗并校验示例数据。",
            "outcome": "",
            "proof_note": "本地课程作业",
            "verified": True,
        },
        {
            "client_id": "evidence-client",
            "kind": "project",
            "title": "SQL 练习",
            "context": "自学记录",
            "actions": "学习 SQL 查询。",
            "outcome": "",
            "proof_note": "",
            "verified": False,
        },
    ):
        assert_success(api_client.post("/api/evidence", json=payload))

    data = assert_success(
        api_client.post(
            "/api/career/compare",
            json={
                "client_id": "evidence-client",
                "role_names": ["数据工程师", "数据分析师"],
            },
        )
    )
    data_engineer = data["items"][0]
    skills_reason = next(
        item["reason"]
        for item in data_engineer["score_breakdown"]
        if item["key"] == "skills"
    )

    assert "Python" not in data_engineer["missing_skills"]
    assert "SQL" in data_engineer["missing_skills"]
    assert "已确认经历证据补充：Python" in skills_reason
