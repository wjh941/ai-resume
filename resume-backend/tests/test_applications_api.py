from __future__ import annotations


def assert_success(response):
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["code"] == "ok"
    return payload["data"]


def application_payload(client_id: str, **changes) -> dict:
    payload = {
        "client_id": client_id,
        "role_name": "数据工程师",
        "company": "[待确认]",
        "city": "上海",
        "source": "官网",
        "status": "applied",
        "applied_at": "2026-08-12",
        "next_action_at": "2026-08-15",
        "interview_notes": "",
        "draft_id": None,
        "notes": "",
    }
    payload.update(changes)
    return payload


def test_application_crud_is_scoped_and_orders_next_actions(api_client):
    first = assert_success(
        api_client.post("/api/applications", json=application_payload("client-a"))
    )
    second = assert_success(
        api_client.post(
            "/api/applications",
            json=application_payload(
                "client-a",
                role_name="数据分析师",
                company="Example",
                source="内推",
                status="interview",
                applied_at="2026-08-11",
                next_action_at="2026-08-13",
                interview_notes="记录真实问题",
            ),
        )
    )

    items = assert_success(
        api_client.get("/api/applications", params={"client_id": "client-a"})
    )["items"]
    assert [item["role_name"] for item in items] == ["数据分析师", "数据工程师"]
    assert assert_success(
        api_client.get("/api/applications", params={"client_id": "client-b"})
    ) == {"items": []}
    assert first["company"] == "[待确认]"

    interview_items = assert_success(
        api_client.get(
            "/api/applications",
            params={"client_id": "client-a", "status": "interview"},
        )
    )["items"]
    assert [item["id"] for item in interview_items] == [second["id"]]

    updated = assert_success(
        api_client.post(
            "/api/applications",
            json=application_payload(
                "client-a",
                id=first["id"],
                company="真实公司",
                status="screening",
                next_action_at="2026-08-14",
            ),
        )
    )
    assert updated["company"] == "真实公司"
    assert updated["status"] == "screening"

    assert_success(
        api_client.delete(
            f"/api/applications/{second['id']}",
            params={"client_id": "client-a"},
        )
    )
    remaining = assert_success(
        api_client.get("/api/applications", params={"client_id": "client-a"})
    )["items"]
    assert [item["id"] for item in remaining] == [first["id"]]


def test_application_rejects_invalid_status_and_cross_client_mutation(api_client):
    saved = assert_success(
        api_client.post("/api/applications", json=application_payload("owner-client"))
    )

    cross_client_update = api_client.post(
        "/api/applications",
        json=application_payload(
            "other-client",
            id=saved["id"],
            company="Not allowed",
        ),
    )
    assert cross_client_update.status_code == 404
    assert cross_client_update.json()["code"] == "not_found"

    cross_client_delete = api_client.delete(
        f"/api/applications/{saved['id']}",
        params={"client_id": "other-client"},
    )
    assert cross_client_delete.status_code == 404

    invalid_status = api_client.post(
        "/api/applications",
        json=application_payload("owner-client", status="unknown"),
    )
    assert invalid_status.status_code == 422
