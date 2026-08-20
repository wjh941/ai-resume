from __future__ import annotations

import sqlite3


def _operator_headers(api_client) -> dict[str, str]:
    token = api_client.headers["Authorization"].split(" ", 1)[1]
    user_id = api_client.app.state.auth_service.verify(token)
    with sqlite3.connect(api_client.app.state.settings.database_path) as connection:
        connection.execute("UPDATE users SET role = 'operator' WHERE user_id = ?", (user_id,))
    user = api_client.app.state.user_repository.get(user_id)
    return {"Authorization": f"Bearer {api_client.app.state.auth_service.issue_token(user)}"}


def test_regular_user_cannot_access_operator_knowledge(api_client) -> None:
    response = api_client.get("/api/operator/knowledge-items")

    assert response.status_code == 403


def test_operator_edits_and_restores_immutable_knowledge_version(api_client) -> None:
    headers = _operator_headers(api_client)
    created = api_client.post(
        "/api/operator/knowledge-items",
        headers=headers,
        json={"title": "面试准备", "content": "初版内容", "status": "active"},
    )
    assert created.status_code == 200
    item = created.json()["data"]
    assert item["version"] == 1

    updated = api_client.patch(
        f"/api/operator/knowledge-items/{item['id']}",
        headers=headers,
        json={"content": "修订内容", "status": "invalid"},
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["version"] == 2
    assert updated.json()["data"]["status"] == "invalid"

    versions = api_client.get(
        f"/api/operator/knowledge-items/{item['id']}/versions", headers=headers
    )
    assert versions.status_code == 200
    assert [version["version"] for version in versions.json()["data"]["items"]] == [2, 1]

    restored = api_client.post(
        f"/api/operator/knowledge-items/{item['id']}/versions/1/restore", headers=headers
    )
    assert restored.status_code == 200
    assert restored.json()["data"]["version"] == 3
    assert restored.json()["data"]["content"] == "初版内容"
    assert restored.json()["data"]["status"] == "active"
