from __future__ import annotations

import json

import pytest

from app.schemas.career import JobPlanResponse
from app.schemas.job import JobIntelligence
from app.services.ai_client import AIServiceError, _coerce_job_intelligence, parse_llm_model
from test_job_plan_api import make_job_plan


def _wrap_fence(payload: str) -> str:
    return f"好的，以下是你要的 JSON：\n```json\n{payload}\n```\n祝求职顺利！"


def test_job_intelligence_tolerates_markdown_fence_and_prose() -> None:
    payload = json.dumps(
        {
            "role_name": "数据分析师",
            "salary_by_experience": {"0-1年": "8K-12K"},
            "responsibilities": ["清洗数据"],
            "hard_requirements": ["SQL"],
            "required_skills": ["Python"],
            "bonus_skills": ["Tableau"],
            "career_route": ["分析师", "高级分析师"],
        },
        ensure_ascii=False,
    )
    intelligence = _coerce_job_intelligence(_wrap_fence(payload))
    assert intelligence.role_name == "数据分析师"
    assert intelligence.salary_by_experience == {"0-1年": "8K-12K"}


def test_job_plan_tolerates_fence_prose_and_outer_text() -> None:
    plan = make_job_plan()
    content = _wrap_fence(json.dumps(plan.model_dump(), ensure_ascii=False))
    parsed = parse_llm_model(content, JobPlanResponse, AIServiceError("ai_invalid_response", "测试"))
    assert parsed.role_name == plan.role_name
    assert len(parsed.sections) == 6


def test_job_plan_unwraps_single_key_envelope() -> None:
    plan = make_job_plan().model_dump()
    content = json.dumps({"job_plan": plan}, ensure_ascii=False)
    parsed = parse_llm_model(content, JobPlanResponse, AIServiceError("ai_invalid_response", "测试"))
    assert parsed.report_scope == "brief"


def test_string_list_fields_flatten_nested_dict_items() -> None:
    plan = make_job_plan().model_dump()
    plan["sections"][0]["items"] = [{"要点": "梳理 SQL 指标口径"}, "监控核心指标"]
    content = json.dumps(plan, ensure_ascii=False)
    parsed = parse_llm_model(content, JobPlanResponse, AIServiceError("ai_invalid_response", "测试"))
    market_items = parsed.sections[0].items
    assert market_items == ["梳理 SQL 指标口径", "监控核心指标"]


def test_untreatable_content_still_raises_invalid() -> None:
    with pytest.raises(AIServiceError):
        parse_llm_model("完全不是 JSON", JobPlanResponse, AIServiceError("ai_invalid_response", "测试"))
    with pytest.raises(AIServiceError):
        _coerce_job_intelligence("```\n也不是 JSON\n```")
