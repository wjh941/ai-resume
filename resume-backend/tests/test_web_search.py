from __future__ import annotations

import httpx
import json
import pytest


def assert_success(response):
    assert response.status_code == 200
    assert response.json()["code"] == "ok"
    return response.json()["data"]


def test_disabled_market_search_returns_readable_fallback(api_client):
    data = assert_success(
        api_client.get("/api/job/market-search", params={"role_name": "数据工程师"})
    )

    assert data["enabled"] is False
    assert data["results"] == []
    assert "联网搜索" in data["notice"]


@pytest.mark.anyio
async def test_tavily_client_sends_query_and_maps_sources():
    captured: dict[str, object] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        captured["authorization"] = request.headers.get("Authorization")
        captured["payload"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "title": "Data engineer market overview",
                        "url": "https://example.com/data-engineer",
                        "content": "Recent public job market summary.",
                        "published_date": "2026-08-01",
                    }
                ]
            },
        )

    from app.services.web_search import TavilyWebSearchClient

    client = TavilyWebSearchClient(
        api_key="tvly-test-key",
        base_url="https://api.tavily.com",
        max_results=5,
        transport=httpx.MockTransport(handler),
    )
    report = await client.search("数据工程师 招聘 要求 薪资")

    assert captured["authorization"] == "Bearer tvly-test-key"
    assert captured["payload"] == {
        "query": "数据工程师 招聘 要求 薪资",
        "max_results": 5,
        "topic": "general",
        "search_depth": "basic",
    }
    assert report.enabled is True
    assert report.provider == "tavily"
    assert report.results[0].title == "Data engineer market overview"
    assert report.results[0].url == "https://example.com/data-engineer"
