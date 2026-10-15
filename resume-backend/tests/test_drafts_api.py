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
    assert hidden.json() == {"code": "not_found", "data": {}, "message": "简历草稿不存在"}

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


def _save_three_drafts(api_client) -> list[str]:
    ids = []
    for index in range(3):
        saved = assert_success(
            api_client.post("/api/draft/save", json=make_draft_payload(job_title=f"Draft {index}"))
        )
        ids.append(saved["id"])
    return ids


def test_draft_list_without_params_keeps_full_array_contract(api_client):
    ids = _save_three_drafts(api_client)

    response = api_client.get("/api/draft/list")
    data = assert_success(response)

    # 旧行为:data 就是草稿对象数组,不是 {items, total} 包装;字段形状不变。
    assert isinstance(data, list)
    assert set(ids) == {draft["id"] for draft in data}
    for draft in data:
        assert set(draft) == {
            "id",
            "job_title",
            "template_id",
            "resume",
            "job_intelligence",
            "created_at",
            "updated_at",
        }


def test_draft_list_pagination_limit_and_offset_slice_in_default_order(api_client):
    _save_three_drafts(api_client)
    full = assert_success(api_client.get("/api/draft/list"))

    first_page = assert_success(api_client.get("/api/draft/list?limit=2&offset=0"))
    assert set(first_page) == {"items", "total", "limit", "offset"}
    assert [draft["id"] for draft in first_page["items"]] == [
        draft["id"] for draft in full[:2]
    ]
    assert first_page["total"] == 3
    assert first_page["limit"] == 2
    assert first_page["offset"] == 0

    second_page = assert_success(api_client.get("/api/draft/list?limit=2&offset=2"))
    assert [draft["id"] for draft in second_page["items"]] == [
        draft["id"] for draft in full[2:]
    ]
    assert second_page["total"] == 3
    assert second_page["offset"] == 2

    # 只传 offset 不传 limit:从 offset 取到底。
    tail = assert_success(api_client.get("/api/draft/list?offset=1"))
    assert [draft["id"] for draft in tail["items"]] == [draft["id"] for draft in full[1:]]
    assert tail["total"] == 3


def test_draft_list_pagination_total_is_user_scoped_and_empty_window_keeps_total(
    api_client, auth_headers
):
    _save_three_drafts(api_client)
    assert_success(
        api_client.post(
            "/api/draft/save",
            json=make_draft_payload("client-b"),
            headers=auth_headers("13900139000"),
        )
    )

    # 越界窗口:items 为空,total 仍返回该用户名下的真实总数(且不含其他用户的草稿)。
    empty_window = assert_success(api_client.get("/api/draft/list?limit=5&offset=10"))
    assert empty_window["items"] == []
    assert empty_window["total"] == 3

    other = api_client.get("/api/draft/list?limit=2", headers=auth_headers("13900139000"))
    other_page = assert_success(other)
    assert other_page["total"] == 1
    assert len(other_page["items"]) == 1
