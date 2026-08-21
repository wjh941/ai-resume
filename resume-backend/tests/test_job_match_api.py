from __future__ import annotations

from conftest import grant_vip


def test_job_match_requires_bearer_auth(api_client):
    api_client.headers.pop("Authorization", None)

    response = api_client.post("/api/job/match", json={})

    assert response.status_code == 401


def test_free_job_match_returns_sorted_preview_without_trusting_profile_payload(api_client):
    response = api_client.post(
        "/api/job/match",
        json={"profile": {"skills": ["FORGED-SKILL"]}, "category": ""},
    )

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert 1 <= len(data["items"]) <= 3
    assert data["limited"] is True
    assert data["items"] == sorted(
        data["items"], key=lambda item: (-item["match_score"], item["role_name"])
    )
    assert all(item["company"] for item in data["items"])
    assert all(item["responsibilities"] for item in data["items"])
    assert "FORGED-SKILL" not in response.text


def test_paid_job_match_unlocks_full_detail_and_filters(api_client):
    grant_vip(api_client, "basic")

    response = api_client.post("/api/job/match", json={"category": "数据"})

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["limited"] is False
    assert data["items"]
    assert all(item["detail_unlocked"] is True for item in data["items"])
    assert all("数据" in item["category"] for item in data["items"])


def test_paid_match_returns_local_mock_sample_detail(api_client):
    grant_vip(api_client, "basic")

    response = api_client.post("/api/job/match", json={"target_role": "数据分析师"})

    assert response.status_code == 200, response.text
    item = next(item for item in response.json()["data"]["items"] if item["role_name"] == "数据分析师")
    assert item["company"] == "澄明数据科技（模拟）"
    assert item["city"] == "上海"
    assert item["salary_range"] == "12k-18k（模拟参考）"
    assert item["responsibilities"] == ["维护业务指标体系", "完成专题数据分析"]
    assert item["requirements"] == ["SQL", "Python", "数据可视化"]
    assert 0 <= item["match_score"] <= 100
