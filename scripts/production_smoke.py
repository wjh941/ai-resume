# -*- coding: utf-8 -*-
"""生产环境冒烟探针：快速验证后端可达性、CORS 白名单与登录链路。

设计为 GitHub Actions 定时任务使用（见 .github/workflows/production-smoke.yml），
也可本地手动运行：
    python scripts/production_smoke.py [--base https://...]
故意不做 AI 调用（定时任务不应消耗中继额度），登录使用演示验证码。
任何一步失败都以非零码退出，让 Actions 标红。
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


async def check(client: httpx.AsyncClient, name: str, ok: bool, detail: str = "") -> bool:
    mark = "PASS" if ok else "FAIL"
    print(f"{mark} {name}" + (f" | {detail}" if detail else ""))
    return ok


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default=DEFAULT_BASE)
    args = parser.parse_args()
    base = args.base.rstrip("/")

    failures = 0
    async with httpx.AsyncClient(timeout=120.0) as client:
        # 1. 健康检查
        try:
            r = await client.get(f"{base}/health")
            ok = r.status_code == 200 and r.json().get("code") == "ok"
            failures += 0 if await check(client, "health", ok, str(r.status_code)) else 1
        except Exception as error:  # noqa: BLE001
            failures += 1
            print(f"FAIL health | {error}")
            print("==== smoke aborted (backend unreachable) ====")
            return 1

        # 2. CORS 白名单：两个真实前端源都必须通过预检
        for origin in REQUIRED_ORIGINS:
            try:
                r = await client.options(
                    f"{base}/api/auth/login-phone",
                    headers={
                        "Origin": origin,
                        "Access-Control-Request-Method": "POST",
                        "Access-Control-Request-Headers": "content-type,authorization",
                    },
                )
                allowed = r.headers.get("access-control-allow-origin") == origin
                failures += 0 if await check(client, f"cors preflight {origin}", allowed, str(r.status_code)) else 1
            except Exception as error:  # noqa: BLE001
                failures += 1
                print(f"FAIL cors preflight {origin} | {error}")

        # 3. 登录链路（演示验证码）
        try:
            r = await client.post(f"{base}/api/auth/send-code", json={"phone": DEMO_PHONE})
            ok = r.status_code == 200 and r.json().get("code") == "ok"
            failures += 0 if await check(client, "send-code", ok, str(r.status_code)) else 1
        except Exception as error:  # noqa: BLE001
            failures += 1
            print(f"FAIL send-code | {error}")

        try:
            r = await client.post(
                f"{base}/api/auth/login-phone",
                json={"phone": DEMO_PHONE, "code": DEMO_CODE},
                headers={"Origin": REQUIRED_ORIGINS[0]},
            )
            token = (r.json().get("data") or {}).get("token")
            failures += 0 if await check(client, "login", r.status_code == 200 and bool(token)) else 1
        except Exception as error:  # noqa: BLE001
            failures += 1
            print(f"FAIL login | {error}")

    print(f"==== production smoke: {'healthy' if failures == 0 else f'{failures} failure(s)'} ====")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
