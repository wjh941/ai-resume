from conftest import make_draft_payload


def assert_success(response):
    assert response.status_code == 200
    assert response.json()["code"] == "ok"
    assert response.json()["message"] == ""
    return response.json()["data"]


def test_draft_crud_is_scoped_to_authenticated_user(api_client, auth_headers):
    saved = assert_success(api_client.post("/api/draft/save", json=make_draft_payload("client-a")))
    draft_id = saved["id"]

    loaded = assert_success(
        api_client.get(f"/api/draft/{draft_id}")
    )
    assert loaded["id"] == draft_id
    assert "client_id" not in loaded
    assert loaded["resume"]["version"] == 1

    hidden = api_client.get(f"/api/draft/{draft_id}", headers=auth_headers("13900139000"))
    assert hidden.status_code == 404
    assert hidden.json() == {"code": "not_found", "data": {}, "message": "Draft not found"}

    removed = assert_success(
        api_client.delete(f"/api/draft/{draft_id}")
    )
    assert removed == {"id": draft_id}
    assert api_client.get(f"/api/draft/{draft_id}").status_code == 404


def test_save_updates_existing_draft_and_list_only_returns_its_users_drafts(api_client, auth_headers):
    source = assert_success(api_client.post("/api/draft/save", json=make_draft_payload("client-a")))
    assert_success(
        api_client.post(
            "/api/draft/save",
            json=make_draft_payload("client-b"),
            headers=auth_headers("13900139000"),
        )
    )

    updated = assert_success(
        api_client.post(
            "/api/draft/save",
            json=make_draft_payload("client-a", id=source["id"], job_title="Platform Engineer"),
        )
    )
    assert updated["id"] == source["id"]
    assert updated["job_title"] == "Platform Engineer"

    drafts = assert_success(api_client.get("/api/draft/list"))
    assert [draft["id"] for draft in drafts] == [source["id"]]
    assert drafts[0]["job_title"] == "Platform Engineer"


def test_copy_creates_independent_draft(api_client):
    source = assert_success(api_client.post("/api/draft/save", json=make_draft_payload()))
    copied = assert_success(
        api_client.post(f"/api/draft/{source['id']}/copy", json={})
    )
    assert copied["id"] != source["id"]
    assert copied["resume"] == source["resume"]

    assert_success(
        api_client.post(
            "/api/draft/save",
            json=make_draft_payload(id=source["id"], job_title="Changed Source"),
        )
    )
    copied_after_source_update = assert_success(
        api_client.get(f"/api/draft/{copied['id']}")
    )
    assert copied_after_source_update["job_title"] == "Data Engineer"
