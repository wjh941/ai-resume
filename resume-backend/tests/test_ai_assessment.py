from __future__ import annotations


def test_assessment_submission_uses_the_configured_ai_client(api_client):
    response = api_client.post(
        "/api/career/assessment/submit",
        json={"answers": {"interest_investigative_1": 5}},
    )

    assert response.status_code == 200
    assert api_client.app.state.ai_client.assessment_query_count == 1
