from __future__ import annotations


def assert_success(response):
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["code"] == "ok"
    return payload["data"]


def test_role_catalog_has_twelve_families_and_at_least_two_hundred_roles(api_client):
    families = assert_success(api_client.get("/api/role/families"))

    assert len(families["items"]) == 12
    assert sum(item["role_count"] for item in families["items"]) >= 200
    family_names = {item["name"] for item in families["items"]}
    assert {"软件研发", "数据与数据平台", "市场、品牌与增长"}.issubset(family_names)


def test_career_profile_round_trip_and_major_suggestions(api_client):
    payload = {
        "client_id": "career-client",
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
    saved = assert_success(api_client.post("/api/career/profile/save", json=payload))
    loaded = assert_success(
        api_client.get("/api/career/profile", params={"client_id": "career-client"})
    )
    majors = assert_success(
        api_client.get("/api/major/suggestions", params={"q": "计算机"})
    )

    assert saved["major"] == "计算机科学与技术"
    assert loaded["skills"] == ["Python", "SQL"]
    assert any(item["major_name"] == "计算机科学与技术" for item in majors["items"])


def test_role_suggestions_match_family_aliases(api_client):
    data = assert_success(
        api_client.get("/api/role/suggestions", params={"q": "数据", "limit": 20})
    )
    family_by_name = {item["role_name"]: item["family"] for item in data["items"]}

    assert {"数据工程师", "数据分析师", "数据治理工程师"}.issubset(family_by_name)
    assert family_by_name["数据工程师"] == "数据与数据平台"
    assert family_by_name["数据标注专员"] == "人工智能与算法"
