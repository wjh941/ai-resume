from __future__ import annotations

from conftest import grant_vip


def _source(role_name: str, title: str, publication_date: str) -> dict[str, object]:
    return {
        "year": 2026,
        "role_name": role_name,
        "scope": "National graduate market",
        "audience": "Graduates",
        "category": "Employment trend",
        "title": title,
        "content": f"Archived summary for {title}.",
        "source_label": f"Archive: {title}",
        "publication_date": publication_date,
        "confidence_note": "Archived source; not a live labor-market fact.",
    }


def _seed_role_and_general_sources(api_client) -> None:
    repository = api_client.app.state.assessment_repository
    repository.save_annual_insight(_source("Data Analyst", "Data analyst archived source", "2026-06-01"))
    repository.save_annual_insight(_source("", "General archived source", "2026-12-01"))


def test_role_query_prioritizes_role_sources_then_general_sources(api_client):
    grant_vip(api_client, "premium")
    _seed_role_and_general_sources(api_client)

    response = api_client.post(
        "/api/career/annual-insights/query",
        json={"role_name": "Data Analyst", "year": 2026, "report_mode": "professional"},
    )

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["role_name"] == "Data Analyst"
    assert data["year"] == 2026
    assert data["report"]["mode"] == "professional"
    assert [item["title"] for item in data["report"]["evidence"]] == [
        "Data analyst archived source",
        "General archived source",
    ]


def test_free_role_query_never_receives_source_evidence(api_client, auth_headers):
    _seed_role_and_general_sources(api_client)

    response = api_client.post(
        "/api/career/annual-insights/query",
        json={"role_name": "Data Analyst", "year": 2026, "report_mode": "professional"},
        headers=auth_headers("13900139000"),
    )

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["report"]["mode"] == "simplified"
    assert data["report"]["evidence"] == []
    assert "Data analyst archived source" not in str(data)


def test_old_annual_insight_endpoints_accept_payload_without_role_name(api_client):
    grant_vip(api_client)
    payload = _source("", "Legacy annual source", "2026-04-01")
    payload.pop("role_name")

    created = api_client.post("/api/career/annual-insights", json=payload)
    listed = api_client.get("/api/career/annual-insights", params={"year": 2026})

    assert created.status_code == 200, created.text
    assert created.json()["data"]["role_name"] == ""
    assert listed.status_code == 200, listed.text
    item = listed.json()["data"]["items"][0]
    assert item["title"] == "Legacy annual source"
    assert item["source_label"] == "Archive: Legacy annual source"
    assert item["publication_date"] == "2026-04-01"


def test_entitled_empty_role_query_reports_only_archive_availability(api_client):
    grant_vip(api_client, "premium")

    response = api_client.post(
        "/api/career/annual-insights/query",
        json={"role_name": "Unarchived Role", "year": 2026, "report_mode": "professional"},
    )

    assert response.status_code == 200, response.text
    report = response.json()["data"]["report"]
    assert report["mode"] == "professional"
    assert report["evidence"] == []
    assert report["summary"] == "暂无可核验年度资料，可先参考岗位基础能力并补充已验证经历。"
