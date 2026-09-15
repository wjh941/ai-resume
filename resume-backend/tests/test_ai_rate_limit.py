from __future__ import annotations

from collections import deque
from time import monotonic

from fastapi.testclient import TestClient

from app.config import load_settings
from app.services.rate_limit import InMemoryRateLimiter


def _client(monkeypatch, tmp_path, *, max_requests: str = "2", window_seconds: str = "60") -> TestClient:
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "ai-rate-limit.db"))
    monkeypatch.setenv("TEMP_FILE_PATH", str(tmp_path / "temp"))
    monkeypatch.setenv("AUTH_DEMO_MODE", "true")
    monkeypatch.setenv("JWT_SECRET", "test-jwt-secret-for-authentication")
    monkeypatch.setenv("AI_RATE_LIMIT_MAX_REQUESTS", max_requests)
    monkeypatch.setenv("AI_RATE_LIMIT_WINDOW_SECONDS", window_seconds)

    from main import create_app
    from test_support import TestAIClient

    client = TestClient(create_app())
    client.app.state.ai_client = TestAIClient()
    return client


def _login(client: TestClient, phone: str) -> dict[str, str]:
    response = client.post("/api/auth/login-phone", json={"phone": phone, "code": "123456"})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['data']['token']}"}


def test_ai_rate_limit_settings_read_configured_env_names(monkeypatch):
    monkeypatch.setenv("AI_RATE_LIMIT_MAX_REQUESTS", "7")
    monkeypatch.setenv("AI_RATE_LIMIT_WINDOW_SECONDS", "42")

    settings = load_settings()

    assert settings.ai_rate_limit_max_requests == 7
    assert settings.ai_rate_limit_window_seconds == 42


def test_ai_endpoint_returns_429_envelope_with_retry_after(monkeypatch, tmp_path):
    with _client(monkeypatch, tmp_path) as client:
        headers = _login(client, "13800138000")
        assert client.post("/api/job/query", json={"role_name": "Data Engineer"}, headers=headers).status_code == 200
        assert client.post("/api/job/query", json={"role_name": "Data Engineer"}, headers=headers).status_code == 200
        limited = client.post("/api/job/query", json={"role_name": "Data Engineer"}, headers=headers)

    assert limited.status_code == 429
    assert limited.json()["code"] == "rate_limited"
    assert limited.json()["message"]
    retry_after = int(limited.headers["retry-after"])
    assert 1 <= retry_after <= 60
    assert limited.headers["x-request-id"]


def test_ai_rate_limit_is_isolated_between_users(monkeypatch, tmp_path):
    with _client(monkeypatch, tmp_path) as client:
        user_a = _login(client, "13800138000")
        user_b = _login(client, "13900139000")

        assert client.post("/api/job/query", json={"role_name": "Data Engineer"}, headers=user_a).status_code == 200
        assert client.post("/api/job/query", json={"role_name": "Data Engineer"}, headers=user_a).status_code == 200
        assert client.post("/api/job/query", json={"role_name": "Data Engineer"}, headers=user_a).status_code == 429

        # 用户 B 的滑动窗口独立计数，不受用户 A 触发限流影响。
        assert client.post("/api/job/query", json={"role_name": "Data Engineer"}, headers=user_b).status_code == 200


def test_default_threshold_keeps_normal_usage_below_limit(api_client):
    # 默认阈值 30 次/60 秒：普通测试（每用例个位数请求）不应触发 429。
    for _ in range(6):
        response = api_client.post("/api/job/query", json={"role_name": "Data Engineer"})
        assert response.status_code == 200, response.text


def test_limiter_reset_clears_windows_for_tests():
    limiter = InMemoryRateLimiter(1, 60)
    assert limiter.check("user-1").allowed
    assert not limiter.check("user-1").allowed

    limiter.reset()

    assert limiter.check("user-1").allowed


def test_limiter_prunes_expired_timestamps_of_checked_key():
    limiter = InMemoryRateLimiter(2, 60)
    stale = monotonic() - 120
    limiter._requests["user-1"] = deque([stale, stale])

    decision = limiter.check("user-1")

    assert decision.allowed
    assert len(limiter._requests["user-1"]) == 1
    assert limiter._requests["user-1"][0] > stale


def test_limiter_purges_expired_keys_when_dict_exceeds_cap():
    limiter = InMemoryRateLimiter(5, 60, max_tracked_keys=2)
    stale = monotonic() - 3600
    for key in ("a", "b", "c"):
        limiter._requests[key] = deque([stale])

    decision = limiter.check("d")

    assert decision.allowed
    assert set(limiter._requests) == {"d"}
