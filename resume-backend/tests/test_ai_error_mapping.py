from __future__ import annotations

import asyncio
from dataclasses import replace

from app.config import load_settings
from app.services.ai_client import build_ai_client
from app.services.career_assessment import assessment_questions


def test_missing_ai_credentials_select_a_friendly_unconfigured_client(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("AI_PROVIDER", "openai_compatible")
    monkeypatch.setenv("AI_API_KEY", "")
    monkeypatch.setenv("AI_MODEL", "")
    settings = replace(load_settings(), ai_api_key="", ai_model="")

    client = build_ai_client(settings)

    assert type(client).__name__ == "UnconfiguredAIClient"


def test_development_without_ai_credentials_returns_deterministic_assessment(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("AI_PROVIDER", "openai_compatible")
    monkeypatch.setenv("AI_API_KEY", "")
    monkeypatch.setenv("AI_MODEL", "")
    settings = replace(load_settings(), app_env="development", ai_api_key="", ai_model="")

    client = build_ai_client(settings)
    result = asyncio.run(client.assess_career(assessment_questions(), {"interest_realistic_1": 5}))

    assert type(client).__name__ == "DevelopmentAIClient"
    assert result["answered_count"] == 1
    assert isinstance(result["action_plan"], dict)
