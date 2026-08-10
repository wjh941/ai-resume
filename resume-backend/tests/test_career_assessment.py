from __future__ import annotations

from app.services.career_assessment import score_assessment


def test_score_assessment_returns_explainable_interest_and_actions():
    result = score_assessment(
        {
            "interest_investigative_1": 5,
            "interest_investigative_2": 5,
            "style_structure_1": 5,
            "style_structure_2": 4,
            "evidence_sql_1": 4,
        }
    )

    assert result["top_interests"][0]["key"] == "investigative"
    assert "结构化" in result["work_style_summary"]
    assert result["strength_evidence"] == ["已说明具备 SQL/数据处理的基础证据"]
    assert len(result["action_plan"]["seven_day"]) >= 2
    assert any("可交付" in item for item in result["action_plan"]["thirty_day"])


def test_score_assessment_does_not_turn_missing_answers_into_strengths():
    result = score_assessment({"interest_social_1": 2})

    assert result["top_interests"] == []
    assert result["strength_evidence"] == []
    assert "证据不足" in result["confidence_note"]
