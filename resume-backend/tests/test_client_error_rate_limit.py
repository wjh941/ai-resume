"""POST /api/system/client-errors 需登录，按用户限流，防止错误日志被灌水。"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import Request
from fastapi.testclient import TestClient

from app.config import load_settings
from app.services.rate_limit import (
    InMemoryRateLimiter,
    RateLimitExceededError,
    enforce_client_error_rate_limit,
)


def _client(monkeypatch, tmp_path, *, max_requests: str = "10") -> TestClient:
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "client-error-limit.db"))
    monkeypatch.setenv("TEMP_FILE_PATH", str(tmp_path / "temp"))
    monkeypatch.setenv("AUTH_DEMO_MODE", "true")
    monkeypatch.setenv("JWT_SECRET", "test-jwt-secret-for-authentication")
    monkeypatch.setenv("CLIENT_ERROR_RATE_LIMIT_MAX_REQUESTS", max_requests)

    from main import create_app

    return TestClient(create_app())


def _login_headers(client: TestClient, phone: str) -> dict[str, str]:
    response = client.post("/api/auth/login-phone", json={"phone": phone, "code": "123456"})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['data']['token']}"}


def test_client_error_settings_read_configured_env_names(monkeypatch):
    monkeypatch.setenv("CLIENT_ERROR_RATE_LIMIT_MAX_REQUESTS", "7")
    monkeypatch.setenv("CLIENT_ERROR_RATE_LIMIT_WINDOW_SECONDS", "42")

    settings = load_settings()

    assert settings.client_error_rate_limit_max_requests == 7
    assert settings.client_error_rate_limit_window_seconds == 42


def test_client_error_endpoint_allows_normal_usage_then_returns_429(monkeypatch, tmp_path):
    client = _client(monkeypatch, tmp_path)
    headers = _login_headers(client, "13800138000")

    for _ in range(10):
        response = client.post(
            "/api/system/client-errors",
            json={"message": "页面发生异常", "component": "render"},
            headers=headers,
        )
        assert response.status_code == 200, response.text

    blocked = client.post(
        "/api/system/client-errors",
        json={"message": "页面发生异常", "component": "render"},
        headers=headers,
    )

    assert blocked.status_code == 429
    assert blocked.json()["code"] == "rate_limited"
    assert blocked.json()["message"]
    assert 1 <= int(blocked.headers["retry-after"]) <= 60
    assert blocked.headers["x-request-id"]


def test_client_error_rate_limit_is_isolated_between_users(monkeypatch, tmp_path):
    client = _client(monkeypatch, tmp_path)
    user_a = _login_headers(client, "13800138000")
    user_b = _login_headers(client, "13900139000")

    for _ in range(10):
        client.post("/api/system/client-errors", json={"message": "boom", "component": "render"}, headers=user_a)

    # 用户 B 的滑动窗口独立计数。
    response = client.post("/api/system/client-errors", json={"message": "boom", "component": "render"}, headers=user_b)
    assert response.status_code == 200


class _FakeApp:
    def __init__(self, limiter: InMemoryRateLimiter) -> None:
        self.state = SimpleNamespace(client_error_rate_limiter=limiter)


def test_client_error_rate_limit_keys_by_request_state_user_id():
    app = _FakeApp(InMemoryRateLimiter(1, 60))

    first = Request({"type": "http", "client": ("203.0.113.9", 12345), "app": app, "state": {"user_id": "user-1"}})
    enforce_client_error_rate_limit(first)

    same_user = Request({"type": "http", "client": ("203.0.113.9", 12345), "app": app, "state": {"user_id": "user-1"}})
    with pytest.raises(RateLimitExceededError):
        enforce_client_error_rate_limit(same_user)


def test_client_error_rate_limit_falls_back_to_client_ip_without_user_id():
    app = _FakeApp(InMemoryRateLimiter(1, 60))

    # 无 user_id 时回落到来源 IP 键。
    enforce_client_error_rate_limit(Request({"type": "http", "client": ("203.0.113.9", 12345), "app": app}))
    with pytest.raises(RateLimitExceededError):
        enforce_client_error_rate_limit(Request({"type": "http", "client": ("203.0.113.9", 12345), "app": app}))


def test_client_error_rate_limit_skips_when_limiter_missing():
    app = SimpleNamespace(state=SimpleNamespace())
    request = Request({"type": "http", "client": ("203.0.113.9", 12345), "app": app})

    # app.state 未挂限流器时放行（与 AI 限流依赖行为一致）。
    enforce_client_error_rate_limit(request)
