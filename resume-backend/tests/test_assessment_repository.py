from __future__ import annotations

from app.db import initialize_database
from app.repositories.assessment import AssessmentRepository


def test_assessment_round_trip_preserves_answers_and_result(tmp_path):
    database_path = tmp_path / "assessment.db"
    initialize_database(database_path)
    repository = AssessmentRepository(database_path)

    repository.save(
        client_id="graduate-client",
        version=1,
        answers={"interest_investigative_1": 5, "style_structure_1": 4},
        result={"interest": {"investigative": 18}, "summary": "偏好分析型任务。"},
    )
    loaded = repository.get("graduate-client")

    assert loaded["client_id"] == "graduate-client"
    assert loaded["answers"]["interest_investigative_1"] == 5
    assert loaded["result"]["summary"] == "偏好分析型任务。"


def test_annual_insights_filter_by_year_and_keep_provenance(tmp_path):
    database_path = tmp_path / "assessment.db"
    initialize_database(database_path)
    repository = AssessmentRepository(database_path)

    repository.save_annual_insight(
        {
            "year": 2024,
            "scope": "national",
            "audience": "graduates",
            "category": "trend",
            "title": "older insight",
            "content": "older archived summary",
            "source_label": "official archive",
            "publication_date": "2024-12-01",
            "confidence_note": "local static summary",
        }
    )
    repository.save_annual_insight(
        {
            "year": 2025,
            "scope": "national",
            "audience": "graduates",
            "category": "trend",
            "title": "current insight",
            "content": "current archived summary",
            "source_label": "official archive",
            "publication_date": "2025-12-01",
            "confidence_note": "local static summary",
        }
    )

    insights = repository.list_annual_insights(2025)

    assert len(insights) == 1
    assert insights[0]["title"] == "current insight"
    assert insights[0]["source_label"] == "official archive"