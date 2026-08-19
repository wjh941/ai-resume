from __future__ import annotations

from conftest import make_draft_payload


def test_account_lifecycle_skeleton_is_authenticated_and_non_destructive(api_client):
    draft = api_client.post("/api/draft/save", json=make_draft_payload())
    assert draft.status_code == 200
    draft_id = draft.json()["data"]["id"]

    scope = api_client.get("/api/account/data-scope")
    assert scope.status_code == 200
    assert "resume_drafts" in scope.json()["data"]["categories"]

    deletion = api_client.post("/api/account/deletion-request")
    export = api_client.post("/api/account/data-export")
    assert deletion.status_code == 200
    assert deletion.json()["data"]["status"] == "requested"
    assert export.status_code == 200
    assert export.json()["data"]["status"] == "not_started"

    preserved = api_client.get(f"/api/draft/{draft_id}")
    assert preserved.status_code == 200


def test_job_favorites_are_owned_by_the_authenticated_user_and_subscription_persists(api_client, auth_headers):
    favorite = api_client.post(
        "/api/job-collection/favorites",
        json={"role_name": "Data Engineer", "note": "Review entry requirements"},
    )
    assert favorite.status_code == 200
    favorite_id = favorite.json()["data"]["id"]

    own_list = api_client.get("/api/job-collection/favorites")
    assert [item["role_name"] for item in own_list.json()["data"]["items"]] == ["Data Engineer"]

    other_list = api_client.get("/api/job-collection/favorites", headers=auth_headers("13900139000"))
    assert other_list.status_code == 200
    assert other_list.json()["data"]["items"] == []

    enabled = api_client.put("/api/job-collection/subscription", json={"enabled": True})
    assert enabled.status_code == 200
    assert enabled.json()["data"]["enabled"] is True
    assert api_client.get("/api/job-collection/subscription").json()["data"]["enabled"] is True

    deleted = api_client.delete(f"/api/job-collection/favorites/{favorite_id}")
    assert deleted.status_code == 200
    assert api_client.get("/api/job-collection/favorites").json()["data"]["items"] == []
