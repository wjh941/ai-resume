from __future__ import annotations


def assert_success(response):
    assert response.status_code == 200, response.text
    return response.json()["data"]


def test_assessment_questions_submit_and_load(api_client):
    questions = assert_success(api_client.get("/api/career/assessment/questions"))
    assert questions["items"]

    saved = assert_success(
        api_client.post(
            "/api/career/assessment/submit",
            json={
                "answers": {
                    "interest_investigative_1": 5,
                    "style_structure_1": 5,
                    "evidence_sql_1": 4,
                },
            },
        )
    )
    loaded = assert_success(
        api_client.get("/api/career/assessment")
    )

    assert saved["result"]["top_interests"][0]["key"] == "investigative"
    assert loaded["answers"]["evidence_sql_1"] == 4


def test_assessment_submission_ignores_forged_client_id(api_client):
    response = api_client.post(
        "/api/career/assessment/submit",
        json={"client_id": "other-user", "answers": {}},
    )

    assert response.status_code == 200


def test_annual_insight_keeps_local_provenance(api_client):
    created = assert_success(
        api_client.post(
            "/api/career/annual-insights",
            json={
                "year": 2025,
                "scope": "全国",
                "audience": "高校毕业生",
                "category": "就业趋势",
                "title": "实践经历准备",
                "content": "来自已归档公开静态摘要的就业准备建议。",
                "source_label": "教育部门公开就业报告",
                "publication_date": "2025-12-01",
                "confidence_note": "本地归档摘要，仅作为职业决策支持。",
            },
        )
    )
    listed = assert_success(api_client.get("/api/career/annual-insights", params={"year": 2025}))

    assert created["source_label"] == "教育部门公开就业报告"
    assert listed["items"][0]["publication_date"] == "2025-12-01"
    assert listed["items"][0]["confidence_note"] == "本地归档摘要，仅作为职业决策支持。"


def test_assessment_submission_rejects_scores_outside_five_point_scale(api_client):
    response = api_client.post(
        "/api/career/assessment/submit",
        json={"answers": {"interest_investigative_1": 6}},
    )

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"
