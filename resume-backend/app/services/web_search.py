from __future__ import annotations

from typing import Protocol

import httpx

from app.config import Settings
from app.schemas.job import MarketSearchReport, MarketSource


class WebSearchClient(Protocol):
    async def search(self, query: str) -> MarketSearchReport: ...


class DisabledWebSearchClient:
    async def search(self, query: str) -> MarketSearchReport:
        del query
        return MarketSearchReport(
            enabled=False,
            provider="disabled",
            notice="未配置联网搜索：当前展示本地岗位目录与 AI 生成的参考信息。",
        )


class TavilyWebSearchClient:
    def __init__(
        self,
        api_key: str,
        base_url: str,
        max_results: int,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._max_results = max(1, min(max_results, 10))
        self._transport = transport

    async def search(self, query: str) -> MarketSearchReport:
        try:
            async with httpx.AsyncClient(timeout=12.0, transport=self._transport) as client:
                response = await client.post(
                    f"{self._base_url}/search",
                    headers={"Authorization": f"Bearer {self._api_key}"},
                    json={
                        "query": query,
                        "max_results": self._max_results,
                        "topic": "general",
                        "search_depth": "basic",
                    },
                )
            response.raise_for_status()
        except httpx.HTTPError:
            return MarketSearchReport(
                enabled=True,
                provider="tavily",
                notice="联网搜索暂时不可用，已保留本地岗位分析结果。",
            )

        payload = response.json()
        results = [
            MarketSource(
                title=str(item.get("title") or "未命名来源"),
                url=str(item.get("url") or ""),
                snippet=str(item.get("content") or item.get("snippet") or ""),
                published_date=_optional_text(item.get("published_date")),
            )
            for item in payload.get("results", [])
            if isinstance(item, dict) and item.get("url")
        ]
        return MarketSearchReport(
            enabled=True,
            provider="tavily",
            notice="联网市场信息来自公开网页，请结合目标城市和企业招聘页进一步核实。",
            results=results,
        )


def build_web_search_client(settings: Settings) -> WebSearchClient:
    if settings.web_search_provider.lower() == "tavily" and settings.tavily_api_key.strip():
        return TavilyWebSearchClient(
            api_key=settings.tavily_api_key,
            base_url=settings.web_search_base_url,
            max_results=settings.web_search_max_results,
        )
    return DisabledWebSearchClient()


def _optional_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None
