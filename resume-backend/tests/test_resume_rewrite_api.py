from copy import deepcopy

from conftest import make_resume_payload


def make_rewrite_payload() -> dict:
    return {
        "resume": make_resume_payload(),
        "job": {
            "version": 1,
            "role_name": "Data Engineer",
            "required_skills": ["Python", "SQL"],
        },
        "mode": "light",
    }


def test_mock_rewrite_changes_descriptions_without_changing_resume_facts(api_client):
    payload = make_rewrite_payload()

    response = api_client.post("/api/resume/ai-rewrite", json=payload)

    assert response.status_code == 200
    assert response.json()["code"] == "ok"


def test_free_resume_rewrite_professional_request_hides_report_evidence(api_client):
    payload = make_rewrite_payload()
    payload["report_mode"] = "professional"

    response = api_client.post("/api/resume/ai-rewrite", json=payload)

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["basic"]
    assert data["report"]["mode"] == "simplified"
    assert data["report"]["evidence"] == []
    rewritten = response.json()["data"]
    assert rewritten["basic"] == payload["resume"]["basic"]
    assert rewritten["education"] == payload["resume"]["education"]
    assert rewritten["employment"][0]["company"] == "Example Company"
    assert rewritten["employment"][0]["description"] != payload["resume"]["employment"][0]["description"]


def test_rewrite_rejects_changed_employer(api_client):
    payload = make_rewrite_payload()
    changed = deepcopy(payload["resume"])
    changed["employment"][0]["company"] = "Different Company"
    api_client.app.state.ai_client.rewrite_result = changed

    result = api_client.post("/api/resume/ai-rewrite", json=payload)

    assert result.status_code == 422
    assert result.json()["code"] == "rewrite_fact_violation"


def test_rewrite_rejects_fabricated_metric(api_client):
    payload = make_rewrite_payload()
    changed = deepcopy(payload["resume"])
    changed["projects"][0]["description"] = "Delivered 40% faster reporting workflow."
    api_client.app.state.ai_client.rewrite_result = changed

    result = api_client.post("/api/resume/ai-rewrite", json=payload)

    assert result.status_code == 422
    assert result.json()["code"] == "rewrite_fact_violation"


def test_rewrite_rejects_changed_english_count_metric(api_client):
    payload = make_rewrite_payload()
    payload["resume"]["projects"][0]["description"] = "Built 3 APIs for 120 customers."
    changed = deepcopy(payload["resume"])
    changed["projects"][0]["description"] = "Built 8 APIs for 500 customers."
    api_client.app.state.ai_client.rewrite_result = changed

    result = api_client.post("/api/resume/ai-rewrite", json=payload)

    assert result.status_code == 422
    assert result.json()["code"] == "rewrite_fact_violation"


def test_rewrite_rejects_changed_chinese_count_metric(api_client):
    payload = make_rewrite_payload()
    payload["resume"]["employment"][0]["description"] = "服务了120名客户，建设3个数据接口。"
    changed = deepcopy(payload["resume"])
    changed["employment"][0]["description"] = "服务了500名客户，建设8个数据接口。"
    api_client.app.state.ai_client.rewrite_result = changed

    result = api_client.post("/api/resume/ai-rewrite", json=payload)

    assert result.status_code == 422
    assert result.json()["code"] == "rewrite_fact_violation"


def test_rewrite_rejects_changed_metric_sign_and_unit(api_client):
    payload = make_rewrite_payload()
    payload["resume"]["projects"][0]["description"] = "Reduced latency by -20% over 120 hours."
    changed = deepcopy(payload["resume"])
    changed["projects"][0]["description"] = "Reduced latency by 20% over 120 days."
    api_client.app.state.ai_client.rewrite_result = changed

    result = api_client.post("/api/resume/ai-rewrite", json=payload)

    assert result.status_code == 422
    assert result.json()["code"] == "rewrite_fact_violation"
