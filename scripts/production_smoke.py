# -*- coding: utf-8 -*-
"""生产环境冒烟探针：快速验证后端可达性、CORS 白名单与登录链路。

设计为 GitHub Actions 定时任务使用（见 .github/workflows/production-smoke.yml），
也可本地手动运行：
    python scripts/production_smoke.py [--base https://...]
故意不做 AI 调用（定时任务不应消耗中继额度），登录使用演示验证码。
任何一步失败都以非零码退出，让 Actions 标红。

对 5xx/网络错误内置重试退避：Render 免费实例的冷启动与瞬时抖动会短暂返回 503，
一次性探测会把这类抖动误报成故障并触发告警邮件（2026-10-14 曾发生）；
重试只吸收"能自愈的抖动"，持续故障仍然会在重试耗尽后如实标红。
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys

import httpx

DEFAULT_BASE = "https://ai-resume-backend-1ouv.onrender.com"
REQUIRED_ORIGINS = (
    "https://ai-resume-workbench.vercel.app",
    "https://wjh941.github.io",
)
DEMO_PHONE = os.getenv("SMOKE_PHONE", "13800138000")
DEMO_CODE = os.getenv("SMOKE_CODE", "123456")

# 每个请求最多 1+4 次尝试,间隔 20s:总窗口约 80s,足够覆盖 Render 冷启动
RETRY_ATTEMPTS = 4
RETRY_BACKOFF_SECONDS = 20.0


async def check(name: str, ok: bool, detail: str = "") -> bool:
    mark = "PASS" if ok else "FAIL"
    print(f"{mark} {name}" + (f" | {detail}" if detail else ""))
    return ok


async def request_with_retry(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    **kwargs,
) -> httpx.Response:
    """5xx 或网络错误时退避重试;4xx 属于确定性响应,不重试直接返回。"""
    for attempt in range(RETRY_ATTEMPTS + 1):
        try:
            response = await client.request(method, url, **kwargs)
        except httpx.TransportError:
            if attempt == RETRY_ATTEMPTS:
                raise
        else:
            if response.status_code < 500 or attempt == RETRY_ATTEMPTS:
                return response
            print(f"retry {attempt + 1}/{RETRY_ATTEMPTS} {method} {url} | HTTP {response.status_code}")
        await asyncio.sleep(RETRY_BACKOFF_SECONDS)
    raise RuntimeError("unreachable")  # pragma: no cover


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default=DEFAULT_BASE)
    args = parser.parse_args()
    base = args.base.rstrip("/")

    failures = 0
    async with httpx.AsyncClient(timeout=120.0) as client:
        # 1. 健康检查
        try:
            r = await request_with_retry(client, "GET", f"{base}/health")
            ok = r.status_code == 200 and r.json().get("code") == "ok"
            failures += 0 if await check("health", ok, str(r.status_code)) else 1
        except Exception as error:  # noqa: BLE001
            failures += 1
            print(f"FAIL health | {error}")
            print("==== smoke aborted (backend unreachable) ====")
            return 1

        # 2. CORS 白名单：两个真实前端源都必须通过预检
        for origin in REQUIRED_ORIGINS:
            try:
                r = await request_with_retry(
                    client,
                    "OPTIONS",
                    f"{base}/api/auth/login-phone",
                    headers={
                        "Origin": origin,
                        "Access-Control-Request-Method": "POST",
                        "Access-Control-Request-Headers": "content-type,authorization",
                    },
                )
                allowed = r.headers.get("access-control-allow-origin") == origin
                failures += 0 if await check(f"cors preflight {origin}", allowed, str(r.status_code)) else 1
            except Exception as error:  # noqa: BLE001
                failures += 1
                print(f"FAIL cors preflight {origin} | {error}")

        # 3. 登录链路（演示验证码）
        try:
            r = await request_with_retry(
                client, "POST", f"{base}/api/auth/send-code", json={"phone": DEMO_PHONE}
            )
            ok = r.status_code == 200 and r.json().get("code") == "ok"
            failures += 0 if await check("send-code", ok, str(r.status_code)) else 1
        except Exception as error:  # noqa: BLE001
            failures += 1
            print(f"FAIL send-code | {error}")

        try:
            r = await request_with_retry(
                client,
                "POST",
                f"{base}/api/auth/login-phone",
                json={"phone": DEMO_PHONE, "code": DEMO_CODE},
                headers={"Origin": REQUIRED_ORIGINS[0]},
            )
            token = (r.json().get("data") or {}).get("token")
            failures += 0 if await check("login", r.status_code == 200 and bool(token)) else 1
        except Exception as error:  # noqa: BLE001
            failures += 1
            print(f"FAIL login | {error}")

    print(f"==== production smoke: {'healthy' if failures == 0 else f'{failures} failure(s)'} ====")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
