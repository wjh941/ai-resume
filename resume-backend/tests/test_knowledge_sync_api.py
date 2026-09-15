from __future__ import annotations

from conftest import operator_headers


def assert_success(response):
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["code"] == "ok"
    return payload["data"]


def test_knowledgebase_write_endpoints_require_operator(api_client):
    forbidden_role = api_client.post(
        "/api/knowledgebase/roles",
        json={
            "role_name": "量子算法实习助理",
            "family": "人工智能与算法",
            "description": "用户手工维护的小众岗位。",
        },
    )
    forbidden_sync = api_client.post("/api/knowledgebase/sync/official")

    assert forbidden_role.status_code == 403
    assert forbidden_sync.status_code == 403
    assert forbidden_role.json()["code"] == "forbidden"
    assert forbidden_sync.json()["code"] == "forbidden"


def test_operator_can_create_manual_role_and_run_official_sync(api_client):
    headers = operator_headers(api_client)

    created = api_client.post(
        "/api/knowledgebase/roles",
        headers=headers,
        json={
            "role_name": "量子算法实习助理",
            "family": "人工智能与算法",
            "description": "用户手工维护的小众岗位。",
        },
    )
    role = assert_success(created)
    assert role["catalog_origin"] == "manual"

    synced = api_client.post("/api/knowledgebase/sync/official", headers=headers)
    data = assert_success(synced)
    assert data["mode"] == "official"
    assert data["status"] in {"completed", "partial", "failed"}
    assert {"run_id", "added_roles", "added_majors", "skipped_rows"} <= data.keys()
    assert "cache_path" not in synced.text


def test_official_sync_keeps_existing_manual_role_unchanged(api_client):
    headers = operator_headers(api_client)
    created = api_client.post(
        "/api/knowledgebase/roles",
        headers=headers,
        json={
            "role_name": "量子算法实习助理",
            "family": "人工智能与算法",
            "description": "用户手工维护的小众岗位。",
        },
    )
    assert_success(created)

    response = api_client.post("/api/knowledgebase/sync/official", headers=headers)
    assert_success(response)

    role = assert_success(
        api_client.get("/api/knowledgebase/roles/量子算法实习助理", headers=headers)
    )
    assert role["catalog_origin"] == "manual"
    assert role["description"] == "用户手工维护的小众岗位。"


def test_source_registry_exposes_only_safe_static_file_metadata(api_client):
    response = api_client.get("/api/knowledgebase/sources")

    data = assert_success(response)

    assert data["items"]
    source = data["items"][0]
    assert source["file_format"] in {"csv", "json", "zip"}
    assert source["parser_kind"] in {"occupation", "major", "employment"}
    assert "cache_path" not in response.text
