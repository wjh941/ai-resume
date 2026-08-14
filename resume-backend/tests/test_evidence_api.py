from conftest import make_resume_payload


def assert_success(response):
    assert response.status_code == 200
    assert response.json()["code"] == "ok"
    return response.json()["data"]


def make_evidence_payload(**changes) -> dict:
    payload = {
        "client_id": "demo-client",
        "kind": "project",
        "title": "Data validation coursework",
        "context": "Database systems course",
        "actions": "Implemented ETL validation rules",
        "outcome": "",
        "proof_note": "Repository screenshot",
        "verified": True,
    }
    payload.update(changes)
    return payload


def test_evidence_api_is_user_scoped_and_generates_pending_safe_suggestions(api_client, auth_headers):
    saved = assert_success(api_client.post("/api/evidence", json=make_evidence_payload()))

    assert "client_id" not in saved
    assert_success(
        api_client.get("/api/evidence", headers=auth_headers("13900139000"))
    ) == {"items": []}

    suggestions = assert_success(
        api_client.post(
            "/api/resume/evidence-suggestions",
            json={"role_name": "Data Engineer"},
        )
    )
    assert suggestions["items"][0]["source_evidence_id"] == saved["id"]
    assert "[待确认]" in suggestions["items"][0]["description"]


def test_evidence_api_updates_and_deletes_only_the_owner_record(api_client, auth_headers):
    saved = assert_success(api_client.post("/api/evidence", json=make_evidence_payload()))

    rejected = api_client.post(
        "/api/evidence",
        json=make_evidence_payload(
            id=saved["id"],
            client_id="other-client",
            title="Should not update",
        ),
        headers=auth_headers("13900139000"),
    )
    assert rejected.status_code == 404
    assert rejected.json()["code"] == "not_found"

    hidden = api_client.delete(
        f"/api/evidence/{saved['id']}",
        headers=auth_headers("13900139000"),
    )
    assert hidden.status_code == 404

    deleted = assert_success(
        api_client.delete(
            f"/api/evidence/{saved['id']}",
        )
    )
    assert deleted == {"id": saved["id"]}


def test_resume_readiness_endpoint_checks_without_mutating_client_payload(api_client):
    resume = make_resume_payload()
    resume["basic"]["name"] = ""
    resume["projects"][0]["description"] = "[待确认] add evidence"

    report = assert_success(
        api_client.post("/api/resume/readiness", json={"resume": resume})
    )

    assert report["ready"] is False
    assert "姓名" in report["blocking_items"]
    assert report["warning_items"]
    assert resume["basic"]["name"] == ""
