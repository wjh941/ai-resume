from __future__ import annotations

from dataclasses import replace

from app.config import load_settings
from app.services.ai_client import build_ai_client


def test_missing_ai_credentials_select_a_friendly_unconfigured_client(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "openai_compatible")
    monkeypatch.setenv("AI_API_KEY", "")
    monkeypatch.setenv("AI_MODEL", "")
    settings = replace(load_settings(), ai_api_key="", ai_model="")

    client = build_ai_client(settings)

    assert type(client).__name__ == "UnconfiguredAIClient"
