from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import math
from threading import Lock
from time import monotonic

from fastapi import Depends, Request

from app.services.auth import current_user_id


@dataclass(frozen=True)
class RateLimitDecision:
    allowed: bool
    retry_after_seconds: int = 0


class RateLimitExceededError(Exception):
    """限流命中时由路由依赖抛出；main.py 统一渲染 429 + rate_limited 信封。"""

    def __init__(self, retry_after_seconds: int) -> None:
        super().__init__("rate limit exceeded")
        self.retry_after_seconds = retry_after_seconds


class InMemoryRateLimiter:
    """Small process-local limiter for public endpoints in the demo deployment."""

    def __init__(
        self,
        max_requests: int,
        window_seconds: int,
        *,
        max_tracked_keys: int = 10_000,
    ) -> None:
        self.max_requests = max(1, max_requests)
        self.window_seconds = max(1, window_seconds)
        self.max_tracked_keys = max(1, max_tracked_keys)
        self._requests: dict[str, deque[float]] = {}
        self._lock = Lock()

    def check(self, key: str) -> RateLimitDecision:
        now = monotonic()
        cutoff = now - self.window_seconds
        with self._lock:
            if len(self._requests) > self.max_tracked_keys:
                self._purge_expired_locked(now)
            timestamps = self._requests.setdefault(key, deque())
            # 惰性清理：被检查 key 中窗口外的时间戳直接丢弃，避免长期驻留。
            while timestamps and timestamps[0] <= cutoff:
                timestamps.popleft()

            if len(timestamps) >= self.max_requests:
                retry_after = max(1, math.ceil(timestamps[0] + self.window_seconds - now))
                return RateLimitDecision(False, retry_after)

            timestamps.append(now)
            return RateLimitDecision(True)

    def reset(self) -> None:
        """测试友好：清空全部滑动窗口，等价于重启进程内的限流状态。"""
        with self._lock:
            self._requests.clear()

    def _purge_expired_locked(self, now: float) -> None:
        cutoff = now - self.window_seconds
        expired_keys: list[str] = []
        for key, timestamps in self._requests.items():
            while timestamps and timestamps[0] <= cutoff:
                timestamps.popleft()
            if not timestamps:
                expired_keys.append(key)
        for key in expired_keys:
            del self._requests[key]


def enforce_ai_rate_limit(
    request: Request,
    user_id: str = Depends(current_user_id),
) -> None:
    """真实消耗 LLM 的端点按 user_id 做滑动窗口限流；阈值随 create_app 注入 app.state。"""
    limiter: InMemoryRateLimiter | None = getattr(request.app.state, "ai_rate_limiter", None)
    if limiter is None:
        return
    decision = limiter.check(user_id)
    if not decision.allowed:
        raise RateLimitExceededError(decision.retry_after_seconds)


def enforce_client_error_rate_limit(request: Request) -> None:
    """客户端错误上报端点按用户限流（路由组装处已注入 JWT 校验并写入 request.state.user_id），
    防止日志被恶意灌水；缺身份信息时回落到来源 IP。"""
    limiter: InMemoryRateLimiter | None = getattr(request.app.state, "client_error_rate_limiter", None)
    if limiter is None:
        return
    user_id = getattr(request.state, "user_id", None)
    client_host = request.client.host if request.client else "unknown"
    decision = limiter.check(str(user_id) if user_id else client_host)
    if not decision.allowed:
        raise RateLimitExceededError(decision.retry_after_seconds)
