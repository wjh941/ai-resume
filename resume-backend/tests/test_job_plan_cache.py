# -*- coding: utf-8 -*-
"""job/query 与 job/plan 的 24h 结果缓存行为：省 AI 调用、可强制刷新、按账号隔离。"""
from __future__ import annotations

import asyncio
import copy

from test_support import TestAIClient


class CountingAIClient:
    """包一层 TestAIClient，统计生成调用次数。"""

    def __init__(self, inner: TestAIClient) -> None:
        self._inner = inner
        self.plan_calls = 0
        self.query_calls = 0

    async def build_job_plan(self, *args, **kwargs):
        self.plan_calls += 1
        return await self._inner.build_job_plan(*args, **kwargs)

    async def query_job(self, *args, **kwargs):
        self.query_calls += 1
        return await self._inner.query_job(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._inner, name)


def install_counter(api_client) -> CountingAIClient:
    counter = CountingAIClient(api_client.app.state.ai_client)
    api_client.app.state.ai_client = counter
    return counter


def test_job_plan_caches_per_user_and_respects_force_refresh(api_client, auth_headers):
    counter = install_counter(api_client)

    first = api_client.post("/api/job/plan", json={"role_name": "Data Engineer"})
    assert first.status_code == 200
    assert first.json()["data"]["cached"] is False
    assert counter.plan_calls == 1

    second = api_client.post("/api/job/plan", json={"role_name": "data  engineer "})
    assert second.status_code == 200
    body = second.json()["data"]
    assert body["cached"] is True
    assert counter.plan_calls == 1, "同账号同参数 24h 内复用缓存，不再触发 AI 生成"
    assert body["sections"] == first.json()["data"]["sections"]
    assert "缓存" in body["cache_notice"]

    refreshed = api_client.post("/api/job/plan", json={"role_name": "Data Engineer", "force_refresh": True})
    assert refreshed.status_code == 200
    assert refreshed.json()["data"]["cached"] is False
    assert counter.plan_calls == 2

    other = api_client.post(
        "/api/job/plan",
        json={"role_name": "Data Engineer"},
        headers=auth_headers("13900139000"),
    )
    assert other.status_code == 200
    assert other.json()["data"]["cached"] is False
    assert counter.plan_calls == 3, "规划是个人化的：不同账号不共享缓存"


def test_job_query_reports_cache_and_force_refresh(api_client):
    counter = install_counter(api_client)

    first = api_client.post("/api/job/query", json={"role_name": "数据分析师"})
    assert first.status_code == 200
    assert first.json()["data"]["cached"] is False
    assert counter.query_calls == 1

    second = api_client.post("/api/job/query", json={"role_name": "数据分析师", "report_mode": "simplified"})
    assert second.status_code == 200
    assert second.json()["data"]["cached"] is True
    assert counter.query_calls == 1

    refreshed = api_client.post("/api/job/query", json={"role_name": "数据分析师", "force_refresh": True})
    assert refreshed.status_code == 200
    assert refreshed.json()["data"]["cached"] is False
    assert counter.query_calls == 2


def test_job_plan_cache_survives_payload_mutation(api_client):
    """缓存返回的是深拷贝语义：修改响应不影响后续缓存命中内容。"""
    install_counter(api_client)
    first = api_client.post("/api/job/plan", json={"role_name": "Product Manager"})
    payload = copy.deepcopy(first.json()["data"])
    payload["role_name"] = "MUTATED"
    second = api_client.post("/api/job/plan", json={"role_name": "Product Manager"})
    assert second.json()["data"]["role_name"] == "Product Manager"
    assert second.json()["data"]["cached"] is True


def test_job_plan_cache_schema_defaults_force_refresh_false():
    from app.schemas.career import JobPlanRequest
    from app.schemas.job import JobQueryRequest

    assert JobPlanRequest(role_name="x").force_refresh is False
    assert JobQueryRequest(role_name="x").force_refresh is False


def test_job_plan_cache_expired_entry_regenerates(api_client):
    """过期条目不命中：把 expires_at 改到过去后应重新生成。"""
    import sqlite3

    counter = install_counter(api_client)
    api_client.post("/api/job/plan", json={"role_name": "Expired Role"})
    assert counter.plan_calls == 1
    with sqlite3.connect(api_client.app.state.settings.database_path) as connection:
        connection.execute("UPDATE job_plan_cache SET expires_at = '2000-01-01T00:00:00+00:00'")
    again = api_client.post("/api/job/plan", json={"role_name": "Expired Role"})
    assert again.status_code == 200
    assert again.json()["data"]["cached"] is False
    assert counter.plan_calls == 2
