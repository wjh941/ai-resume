from __future__ import annotations


def test_job_plan_requires_bearer_auth(api_client):
    api_client.headers.pop("Authorization", None)
    response = api_client.post("/api/job/plan", json={"role_name": "Data Engineer"})
    assert response.status_code == 401
