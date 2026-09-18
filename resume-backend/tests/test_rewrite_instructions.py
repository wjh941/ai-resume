# -*- coding: utf-8 -*-
"""自定义指令 AI 改写：schema 约束、prompt 注入、事实守卫共存。"""
from __future__ import annotations

import asyncio
import json

import pytest
from pydantic import ValidationError

from app.config import Settings
from app.schemas.job import JobIntelligence, ResumeRewriteRequest
from app.schemas.resume import ResumePayload
from app.services.ai_client import OpenAICompatibleClient
from conftest import make_resume_payload


def _request(instructions) -> ResumeRewriteRequest:
    return ResumeRewriteRequest(
        resume=make_resume_payload(),
        job={"version": 1, "role_name": "Data Engineer", "required_skills": ["Python"]},
        mode="light",
        instructions=instructions,
    )


def test_instructions_default_none_and_blank_becomes_none():
    assert _request(None).instructions is None
    assert _request("   ").instructions is None


def test_instructions_reject_over_200_chars():
    with pytest.raises(ValidationError):
        _request("突" * 201)


def test_instructions_strip_newlines_and_collapse_whitespace():
    assert _request("突出项目管理经验\n\n压缩到一页\t语气  谦逊").instructions == "突出项目管理经验 压缩到一页 语气 谦逊"


class CapturingRewriteClient(OpenAICompatibleClient):
    def __init__(self, response: str) -> None:
        super().__init__(
            Settings(
                app_env="test",
                app_host="127.0.0.1",
                app_port=8000,
                database_path=None,  # type: ignore[arg-type]
                ai_provider="openai_compatible",
                ai_api_key="test",
                ai_base_url="https://example.invalid/v1",
                ai_model="test",
                cache_expire_day=7,
                temp_file_path=None,  # type: ignore[arg-type]
                export_file_expire_minutes=60,
                pdf_renderer="playwright",
                playwright_browsers_path="",
            )
        )
        self.calls: list[tuple[str, str]] = []
        self._response = response

    async def _chat_completion(self, system_prompt: str, user_prompt: str) -> str:
        self.calls.append((system_prompt, user_prompt))
        return self._response


def _client() -> CapturingRewriteClient:
    return CapturingRewriteClient(json.dumps(make_resume_payload(), ensure_ascii=False))


def test_instructions_are_injected_into_rewrite_prompt():
    client = _client()
    asyncio.run(client.rewrite_resume(
        ResumePayload.model_validate(make_resume_payload()),
        JobIntelligence.model_validate({"version": 1, "role_name": "Data Engineer", "required_skills": ["Python"]}),
        "light",
        "突出项目管理经验",
    ))
    system_prompt, _ = client.calls[0]
    assert "突出项目管理经验" in system_prompt
    assert "no-fabrication rule" in system_prompt


def test_rewrite_without_instructions_keeps_clean_prompt():
    client = _client()
    asyncio.run(client.rewrite_resume(
        ResumePayload.model_validate(make_resume_payload()),
        JobIntelligence.model_validate({"version": 1, "role_name": "Data Engineer", "required_skills": ["Python"]}),
        "light",
    ))
    system_prompt, _ = client.calls[0]
    assert "custom requirements" not in system_prompt


def test_envelope_echo_response_is_unwrapped():
    """部分中继把整个输入信封回显而非裸 ResumePayload——应提取 resume 后解析。"""
    envelope = {
        "mode": "light",
        "resume": make_resume_payload(),
        "target_job": {"version": 1, "role_name": "Data Engineer", "required_skills": ["Python"]},
    }
    client = CapturingRewriteClient(json.dumps(envelope, ensure_ascii=False))
    result = asyncio.run(client.rewrite_resume(
        ResumePayload.model_validate(make_resume_payload()),
        JobIntelligence.model_validate({"version": 1, "role_name": "Data Engineer", "required_skills": ["Python"]}),
        "light",
    ))
    assert result.basic.name == make_resume_payload()["basic"]["name"]


def test_fact_guard_survives_instructions_at_api_level(api_client):
    from copy import deepcopy

    payload = {
        "resume": make_resume_payload(),
        "job": {"version": 1, "role_name": "Data Engineer", "required_skills": ["Python"]},
        "mode": "light",
        "instructions": "突出项目管理经验",
    }
    ok = api_client.post("/api/resume/ai-rewrite", json=payload)
    assert ok.status_code == 200
    assert "Custom: 突出项目管理经验" in ok.json()["data"]["employment"][0]["description"]

    fabricated = deepcopy(payload)
    fabricated["resume"]["projects"][0]["description"] = "Delivered 3 APIs."
    changed = deepcopy(fabricated)
    changed["resume"]["projects"][0]["description"] = "Delivered 8 APIs."
    api_client.app.state.ai_client.rewrite_result = changed["resume"]

    guarded = api_client.post("/api/resume/ai-rewrite", json=fabricated)
    assert guarded.status_code == 422
    assert guarded.json()["code"] == "rewrite_fact_violation"
