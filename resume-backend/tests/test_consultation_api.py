from __future__ import annotations


def assert_success(response):
    assert response.status_code == 200
    assert response.json()["code"] == "ok"
    return response.json()["data"]


def test_job_analysis_returns_eight_sections_and_identity_specific_plan(api_client):
    data = assert_success(
        api_client.post(
            "/api/consultation/job-analysis",
            json={"role_name": "Data Engineer", "identity_code": "2"},
        )
    )

    assert data["identity_code"] == "2"
    assert data["identity_label"] == "应届毕业生（秋招/春招）"
    assert len(data["job_analysis_sections"]) == 8
    assert [section["order"] for section in data["job_analysis_sections"]] == list(range(1, 9))
    assert data["job_analysis_sections"][0]["title"] == "基础概况"
    assert data["job_analysis_sections"][7]["title"] == "岗位优缺点"
    assert data["identity_plan"]["title"] == "应届生专属简历&求职实操方案"
    assert len(data["identity_plan"]["sections"]) >= 4
    assert data["job_intelligence"]["role_name"] == "Data Engineer"


def test_job_analysis_rejects_unknown_identity_code(api_client):
    response = api_client.post(
        "/api/consultation/job-analysis",
        json={"role_name": "Data Engineer", "identity_code": "6"},
    )

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"


def test_resume_review_returns_only_review_sections(api_client):
    data = assert_success(
        api_client.post(
            "/api/consultation/resume-review",
            json={
                "identity_code": "5",
                "role_name": "Data Engineer",
                "resume_text": "曾负责团队日常数据整理和报表制作。",
            },
        )
    )

    assert data["identity_code"] == "5"
    assert data["identity_label"] == "零基础跨行业转行"
    assert data["issues"]
    assert data["rewrite_examples"]
    assert data["keywords"]
    assert "job_analysis_sections" not in data
    assert "identity_plan" not in data
    assert "待确认" in " ".join(data["rewrite_examples"])


def test_resume_review_rejects_blank_text(api_client):
    response = api_client.post(
        "/api/consultation/resume-review",
        json={"identity_code": "1", "resume_text": "   "},
    )

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"
