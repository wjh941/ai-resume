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
    assert all(item["company"] == "本地岗位库参考" for item in data["items"])
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
