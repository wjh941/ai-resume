from __future__ import annotations

from conftest import make_draft_payload


def test_representative_business_routes_reject_missing_bearer_tokens(api_client):
    api_client.headers.pop("Authorization")
    paths = (
        "/api/template/list",
        "/api/draft/list",
        "/api/evidence",
        "/api/applications",
        "/api/career/assessment/questions",
        "/api/role/families",
        "/api/job/suggestions?q=data",
        "/api/knowledgebase/sources",
        "/downloads/missing",
    )

    for path in paths:
        assert api_client.get(path).status_code == 401, path


def test_second_authenticated_user_cannot_read_a_first_users_draft(api_client, auth_headers):
    owner_headers = auth_headers("13800138000")
    other_headers = auth_headers("13900139000")
    saved = api_client.post(
        "/api/draft/save",
        json=make_draft_payload(client_id="forged-client-id"),
        headers=owner_headers,
    )

    assert saved.status_code == 200
    draft_id = saved.json()["data"]["id"]
    response = api_client.get(f"/api/draft/{draft_id}", headers=other_headers)

    assert response.status_code == 404
