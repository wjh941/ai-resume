from __future__ import annotations

from conftest import make_draft_payload


def test_resume_version_snapshot_compare_restore_and_import_skeleton(api_client) -> None:
    draft = api_client.post("/api/draft/save", json=make_draft_payload()).json()["data"]
    first = api_client.post(
        f"/api/draft/{draft['id']}/versions", json={"note": "投递前"}
    )
    assert first.status_code == 200, first.text

    changed = api_client.post(
        "/api/draft/save",
        json=make_draft_payload(id=draft["id"], job_title="后端工程师"),
    )
    assert changed.status_code == 200, changed.text
    second = api_client.post(
        f"/api/draft/{draft['id']}/versions", json={"note": "调整后"}
    )
    assert second.status_code == 200, second.text

    comparison = api_client.get(
        f"/api/draft/{draft['id']}/versions/compare",
        params={
            "left_id": first.json()["data"]["id"],
            "right_id": second.json()["data"]["id"],
        },
    )
    restored = api_client.post(
        f"/api/draft/{draft['id']}/versions/{first.json()['data']['id']}/restore"
    )
    versions = api_client.get(f"/api/draft/{draft['id']}/versions")
    importer = api_client.post(f"/api/draft/{draft['id']}/import")

    assert comparison.status_code == restored.status_code == versions.status_code == 200
    assert "job_title" in comparison.json()["data"]["changed_fields"]
    assert restored.json()["data"]["job_title"] == "Data Engineer"
    assert next(item for item in versions.json()["data"]["items"] if item["id"] == first.json()["data"]["id"])["is_active"] is True
    assert importer.status_code == 501
