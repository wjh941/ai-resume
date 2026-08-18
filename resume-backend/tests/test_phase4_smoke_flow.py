from __future__ import annotations

from conftest import make_draft_payload


def test_phase4_authenticated_resume_career_export_and_permission_flow(api_client):
    health = api_client.get("/health/detail")
    assert health.status_code == 200
    assert health.json()["data"]["database"]["status"] == "connected"

    draft = api_client.post("/api/draft/save", json=make_draft_payload())
    assert draft.status_code == 200
    draft_id = draft.json()["data"]["id"]

    profile = api_client.post(
        "/api/career/profile/save",
        json={
            "client_id": "phase4-smoke",
            "identity_code": "2",
            "major": "Computer Science",
            "education_level": "Bachelor",
            "skills": ["Python", "SQL"],
        },
    )
    assert profile.status_code == 200
    plan = api_client.post("/api/career/recommend", params={"client_id": "phase4-smoke"})
    assert plan.status_code == 200
    assert plan.json()["data"]["tiers"]["stable"]

    export = api_client.post("/api/export/word", json={"draft_id": draft_id})
    assert export.status_code == 200
    assert export.json()["data"]["filename"].endswith(".docx")

    api_client.headers.pop("Authorization")
    denied = api_client.post("/api/export/word", json={"draft_id": draft_id})
    assert denied.status_code == 401
