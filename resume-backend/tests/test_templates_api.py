def test_template_list_returns_the_four_seeded_templates_in_a_success_envelope(api_client, auth_headers):
    response = api_client.get("/api/template/list", headers=auth_headers())

    assert response.status_code == 200
    assert response.json()["code"] == "ok"
    assert response.json()["message"] == ""
    templates = response.json()["data"]
    assert [template["id"] for template in templates] == [
        "business",
        "technology",
        "graduate",
        "analytics",
    ]
    assert all(template["name"] and template["description"] for template in templates)


def test_health_reports_a_success_envelope(api_client):
    response = api_client.get("/health")

    assert response.status_code == 200
    assert response.json()["code"] == "ok"
    assert response.json()["message"] == ""
    assert response.json()["data"]["status"] == "healthy"
    assert {"job_plan", "job_match", "ai_setup"}.issubset(response.json()["data"]["capabilities"])
