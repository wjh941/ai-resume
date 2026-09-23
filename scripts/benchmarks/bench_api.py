# -*- coding: utf-8 -*-
"""ai-resume 接口基准测试 runner（实测 README「性能」小节的数据来源）。

设计原则：
- 压测对象必须是隔离实例：独立 SQLite 文件、独立端口、调高的限流阈值，
  绝不打本机 8000 开发实例或线上 Render 实例。启动方式见同目录 start-bench-backend.ps1。
- 除 httpx（后端 requirements.txt 已有）外零新增依赖，任何拿到仓库的人都能复现。
- 输出 Markdown 表格，直接可贴进 docs/benchmarks.md。

用法（PowerShell，仓库根目录）：
  powershell -File scripts/benchmarks/start-bench-backend.ps1   # 启动 127.0.0.1:8004 隔离实例
  resume-backend\\.venv\\Scripts\\python.exe scripts/benchmarks/bench_api.py --base http://127.0.0.1:8004

可选参数：
  --draft-count 1000     预置简历草稿条数（VIP 用户无上限）
  --samples 30           每个读接口的采样次数
  --ai-users 5           AI 润色并发用户数（消耗真实 AI 配额，可用 --skip-ai 关闭）
  --skip-ai              跳过真实 AI 接口阶段
  --out docs/benchmarks.md  把 Markdown 结果追加写入文件
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sqlite3
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

AUTH_RATE_LIMIT_HEADROOM = 200  # 压测实例已通过环境变量调高限流，这里只是自我约束


# ---------------------------------------------------------------- 统计与输出


class Phase:
    def __init__(self, name: str, samples: list[float], failures: list[str],
                 extra: dict | None = None):
        self.name = name
        self.samples = samples
        self.failures = failures
        self.extra = extra or {}

    @property
    def ok(self) -> int:
        return len(self.samples)

    def row(self) -> list[str]:
        if not self.samples:
            return [self.name, "0", "-", "-", "-", "-", "-", str(len(self.failures)),
                    self.extra.get("note", "")]
        xs = sorted(self.samples)
        p = lambda q: xs[min(len(xs) - 1, int(round(q * (len(xs) - 1))))]
        return [
            self.name,
            str(self.ok),
            f"{p(0.50):.1f}",
            f"{p(0.95):.1f}",
            f"{p(0.99):.1f}",
            f"{max(xs):.1f}",
            f"{statistics.fmean(xs):.1f}",
            str(len(self.failures)),
            self.extra.get("note", ""),
        ]

    @staticmethod
    def header() -> str:
        return (
            "| 接口场景 | 成功样本 | P50 (ms) | P95 (ms) | P99 (ms) | max (ms) | 均值 (ms) | 失败 | 备注 |\\n"
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"
        )


def recordfail(failures: list[str], label: str, status: int, body: str) -> None:
    failures.append(f"{label} HTTP {status}: {body[:120]}")


# ---------------------------------------------------------------- 客户端封装


class Api:
    def __init__(self, base: str, token: str | None = None, timeout: float = 30.0):
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        # trust_env=False：本机 Clash 等代理会劫持 127.0.0.1 请求（smoke_e2e.py 同款教训）
        self.client = httpx.AsyncClient(base_url=base, headers=headers,
                                        trust_env=False, timeout=timeout)

    async def post(self, path: str, payload: dict, label: str,
                   failures: list[str]) -> tuple[float, dict | None]:
        t0 = time.perf_counter()
        try:
            resp = await self.client.post(path, json=payload)
        except httpx.HTTPError as error:
            failures.append(f"{label} 网络异常: {type(error).__name__}: {error}")
            return (time.perf_counter() - t0) * 1000, None
        ms = (time.perf_counter() - t0) * 1000
        if resp.status_code != 200:
            recordfail(failures, label, resp.status_code, resp.text)
            return ms, None
        body = resp.json()
        if body.get("code") not in (None, "ok"):
            failures.append(f"{label} code={body.get('code')}")
            return ms, None
        return ms, body

    async def get(self, path: str, label: str,
                  failures: list[str]) -> tuple[float, dict | None, int]:
        t0 = time.perf_counter()
        try:
            resp = await self.client.get(path)
        except httpx.HTTPError as error:
            failures.append(f"{label} 网络异常: {type(error).__name__}: {error}")
            return (time.perf_counter() - t0) * 1000, None, 0
        ms = (time.perf_counter() - t0) * 1000
        if resp.status_code != 200:
            recordfail(failures, label, resp.status_code, resp.text)
            return ms, None, 0
        body = resp.json()
        if body.get("code") not in (None, "ok"):
            failures.append(f"{label} code={body.get('code')}")
            return ms, None, 0
        return ms, body, len(resp.content)


async def login(api_base: str, phone: str) -> str:
    """演示验证码登录，返回 JWT。"""
    async with httpx.AsyncClient(base_url=api_base, trust_env=False, timeout=30.0) as c:
        await c.post("/api/auth/send-code", json={"phone": phone})
        r = await c.post("/api/auth/login-phone", json={"phone": phone, "code": "123456"})
        r.raise_for_status()
        data = r.json()["data"]
        return data["token"]


# ---------------------------------------------------------------- 业务负载


def make_resume(seq: int) -> dict:
    return {
        "version": 1,
        "basic": {"name": f"压测用户{seq}", "phone": "13900001234",
                  "email": f"bench{seq}@example.com", "city": "北京"},
        "job": {"target_role": "数据分析师", "employment_type": "full_time",
                "expected_salary": "20k-30k"},
        "education": [{"school": "示例大学", "major": "计算机科学", "degree": "本科",
                       "start_date": "2020-09", "end_date": "2024-06", "courses": ""}],
        "employment": [{"company": f"示例公司{seq}", "position": "数据分析师",
                        "start_date": "2024-07", "end_date": "2025-01",
                        "description": "搭建日报数据管道，产出经营指标报表。"}],
        "projects": [{"name": f"用户行为分析项目{seq}", "role": "负责人",
                      "start_date": "2024-03", "end_date": "2024-06",
                      "description": "分析 100 万条埋点日志，输出转化漏斗与留存报告。"}],
        "skills": {"skills": ["Python", "SQL", "Tableau"], "certificates": []},
        "self_evaluation": "对数据敏感，习惯用数据驱动决策。",
        "section_visibility": {"basic": True, "job": True, "education": True,
                               "employment": True, "projects": True, "skills": True,
                               "self_evaluation": True},
    }


def draft_payload(seq: int) -> dict:
    return {"client_id": "bench-client", "job_title": "数据分析师",
            "template_id": "analytics", "resume": make_resume(seq)}


def grant_vip(db_path: str, user_id: str) -> None:
    """给压测用户发 premium 会员（解除 3 份草稿上限），与 tests/conftest.py 同款写法。"""
    now = datetime.now(timezone.utc).isoformat()
    expire = "2099-12-31T00:00:00+00:00"
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO user_vip (user_id, vip_level, expire_time, auto_renew, create_time)
            VALUES (?, 'premium', ?, 0, ?)
            ON CONFLICT(user_id) DO UPDATE SET
              vip_level = 'premium', expire_time = excluded.expire_time, auto_renew = 0
            """,
            (user_id, expire, now),
        )


# ---------------------------------------------------------------- 各阶段


async def phase_auth(api_base: str, n: int) -> Phase:
    """登录链路：send-code + login-phone 换 JWT（计时含两次往返）。"""
    samples, failures = [], []
    for i in range(n):
        phone = f"1391{i:08d}"[:11]
        api = Api(api_base)
        t0 = time.perf_counter()
        await api.post("/api/auth/send-code", {"phone": phone}, "send-code", failures)
        ms, body = await api.post("/api/auth/login-phone",
                                  {"phone": phone, "code": "123456"}, "login-phone", failures)
        await api.client.aclose()
        if body:
            samples.append((time.perf_counter() - t0) * 1000)
    return Phase("登录全链路（send-code + login-phone）", samples, failures)


async def phase_seed_drafts(api: Api, n: int, concurrency: int = 4) -> Phase:
    """预置 n 份草稿（VIP 无上限），本身也是一次写接口压测。"""
    sem = asyncio.Semaphore(concurrency)
    failures: list[str] = []
    samples: list[float] = []

    async def one(i: int) -> None:
        async with sem:
            ms, _ = await api.post("/api/draft/save", draft_payload(i),
                                   f"draft/save#{i}", failures)
            if _ is not None:
                samples.append(ms)

    t0 = time.perf_counter()
    await asyncio.gather(*(one(i) for i in range(n)))
    wall = time.perf_counter() - t0
    note = f"并发写入 {concurrency}，共 {n} 条耗时 {wall:.1f}s（{n / wall:.1f} req/s）"
    return Phase("草稿写入 draft/save（建库阶段）", samples, failures, {"note": note})


async def phase_read(api: Api, label: str, method: str, path: str,
                     payload: dict | None, n: int, note: str = "") -> Phase:
    samples, failures = [], []
    size = 0
    for _ in range(n):
        if method == "GET":
            ms, body, nbytes = await api.get(path, label, failures)
        else:
            ms, body = await api.post(path, payload, label, failures)
            nbytes = 0
        if body is not None:
            samples.append(ms)
            size = max(size, nbytes)
    extra = {"note": note}
    if size:
        extra["note"] = f"{note} 最大响应体 {size / 1024:.0f}KB".strip()
    return Phase(label, samples, failures, extra)


async def phase_ai_rewrite(api_base: str, baseline_user: str, users: list[str],
                           concurrency: int, baseline_rounds: int = 2) -> tuple[Phase, Phase]:
    """真实 AI 润色：单用户基线 N 次，再并发用户同时发起，观察排队放大。

    事实守卫（rewrite_fact_violation）是产品语义：上游模型试图改动不可变更事实时
    被后端拦截并计为一次"守卫拦截"，不算客户端失败，单独计数写入备注。
    """
    make_api = lambda token: Api(api_base, token, timeout=240.0)
    payload = {"resume": make_resume(0), "job": {"role_name": "数据分析师"},
               "mode": "light", "instructions": "", "report_mode": "simplified"}
    failures: list[str] = []
    guarded = {"count": 0}

    async def call_once(token: str) -> float | None:
        api = make_api(token)
        local_failures: list[str] = []
        try:
            ms, body = await api.post("/api/resume/ai-rewrite", payload,
                                      "ai-rewrite", local_failures)
            if body is None:
                # 守卫拦截是预期行为而非故障，从失败里挪到计数
                if any("rewrite_fact_violation" in f for f in local_failures):
                    guarded["count"] += 1
                    return None
                failures.extend(local_failures)
                raise AiCallError("ai-rewrite failed")
            return ms
        finally:
            await api.client.aclose()

    baseline_samples: list[float] = []
    for _ in range(baseline_rounds):
        try:
            ms = await call_once(baseline_user)
        except AiCallError:
            continue  # 失败明细已在 failures 里，保留继续下一轮
        if ms is not None:
            baseline_samples.append(ms)
    baseline = Phase("AI 润色 light（单用户基线）", baseline_samples, list(failures),
                     {"note": _ai_note(guarded["count"], baseline_rounds)})

    if not baseline_samples:
        # 基线全挂（通常是上游模型方差不达标）：如实记录并跳过并发回合
        concurrent = Phase(f"AI 润色 light（{concurrency} 用户并发）", [], [],
                           {"note": "基线回合全部失败，跳过并发排队观察，见失败明细"})
        return baseline, concurrent

    failures_before = len(failures)
    t0 = time.perf_counter()
    results = await asyncio.gather(*(call_once(t) for t in users[:concurrency]),
                                   return_exceptions=True)
    wall = time.perf_counter() - t0
    samples = [r for r in results if isinstance(r, float)]
    for r in results:
        if isinstance(r, Exception) and not isinstance(r, AiCallError):
            failures.append(f"并发请求异常: {r}")
    concurrent_failures = failures[failures_before:]
    note = _ai_note(guarded["count"], concurrency)
    if samples:
        note += (f"；{concurrency} 用户同时发起，全部返回耗时 {wall:.1f}s，"
                 f"相对单用户基线放大 {wall / (statistics.fmean(baseline_samples) / 1000):.1f}x")
    else:
        note += f"；并发回合无成功样本可统计排队放大（总耗时 {wall:.1f}s）"
    return baseline, Phase(f"AI 润色 light（{concurrency} 用户并发）", samples,
                           concurrent_failures, {"note": note})


def _ai_note(guarded: int, attempts: int) -> str:
    note = "真实模型调用，含网络与模型推理耗时"
    if guarded:
        note += f"；事实守卫拦截 {guarded}/{attempts} 次不合规改写（预期行为）"
    return note


class AiCallError(RuntimeError):
    pass


# ---------------------------------------------------------------- 主流程


async def run(args: argparse.Namespace) -> str:
    api_base = args.base.rstrip("/")
    started = datetime.now()
    lines: list[str] = []
    phases: list[Phase] = []

    # 0. 健康检查 + 主用户登录
    probe = Api(api_base)
    ms, health, _ = await probe.get("/health", "health", [])
    if health is None:
        print(f"后端不可用：{api_base}/health 请先用 start-bench-backend.ps1 启动隔离实例", file=sys.stderr)
        raise SystemExit(2)
    await probe.client.aclose()

    main_token = await login(api_base, "13900001234")
    grant_vip(args.db, _user_id_of(api_base, main_token))  # 解除草稿上限
    api = Api(api_base, main_token)
    # 职业规划接口要求先有职业画像（负载与 scripts/smoke_e2e.py 保持一致）
    await api.post("/api/career/profile/save",
                   {"identity_code": "1", "major": "计算机科学", "education_level": "本科",
                    "city_preferences": ["北京"], "industry_preferences": ["互联网"],
                    "skills": ["Python", "SQL", "Tableau"]},
                   "career/profile/save", [])

    # 1. 登录链路
    phases.append(await phase_auth(api_base, args.samples))

    # 2. 预置草稿 + 写入压测
    seed_phase = await phase_seed_drafts(api, args.draft_count)
    phases.append(seed_phase)

    # 3. 读接口
    phases.append(await phase_read(api, f"草稿列表 draft/list（{args.draft_count} 条全量）",
                                   "GET", "/api/draft/list", None, args.samples))
    phases.append(await phase_read(api, "草稿写入 draft/save（稳态追加）", "POST",
                                   "/api/draft/save", draft_payload(10_000), args.samples))
    phases.append(await phase_read(api, "简历就绪检查 resume/readiness", "POST",
                                   "/api/resume/readiness",
                                   {"resume": make_resume(0)}, args.samples * 2))
    phases.append(await phase_read(api, "职业规划 career/recommend", "POST",
                                   "/api/career/recommend",
                                   {"identity_code": "1", "major": "计算机科学",
                                    "education_level": "本科", "city_preferences": ["北京"],
                                    "skills": ["Python", "SQL"]}, args.samples))
    phases.append(await phase_read(api, "岗位匹配 job/match（本地目录）", "POST",
                                   "/api/job/match",
                                   {"target_role": "数据分析师", "report_mode": "simplified"},
                                   args.samples))

    # 4+5. 真实 AI 阶段：预热岗位缓存 + 润色基线/并发。失败只记档，不丢已完成结果。
    if not args.skip_ai:
        try:
            warm = Api(api_base, main_token)
            warm_ms, _ = await warm.post("/api/job/query", {"role_name": "数据分析师"},
                                         "job/query(warm)", [])
            await warm.client.aclose()
            warm_note = f"首次调用真实 AI 预热，耗时 {warm_ms:.0f}ms" if warm_ms else ""
            phases.append(await phase_read(api, "岗位查询 job/query（缓存命中）", "POST",
                                           "/api/job/query", {"role_name": "数据分析师"},
                                           args.samples * 2, warm_note))

            ai_users = [await login(api_base, f"13900002{i:03d}")
                        for i in range(1, args.ai_users + 1)]
            baseline, concurrent = await phase_ai_rewrite(api_base, main_token, ai_users,
                                                          args.ai_users)
            phases.append(baseline)
            phases.append(concurrent)
        except Exception as error:  # noqa: BLE001 —— AI 不可用不能让整份报告丢失
            phases.append(Phase("AI 阶段（未完成，见失败明细）", [],
                                [f"{type(error).__name__}: {error}"]))

    await api.client.aclose()

    # 6. 汇总输出
    lines.append("## ai-resume 接口基准测试")
    lines.append("")
    lines.append(f"- 时间：{started.strftime('%Y-%m-%d %H:%M')}（本地时区）  ")
    lines.append(f"- 被测实例：`{api_base}`（本机隔离实例，见 scripts/benchmarks/start-bench-backend.ps1）  ")
    lines.append(f"- 数据规模：{args.draft_count} 份简历草稿（premium 账号）；单进程 uvicorn + SQLite(WAL)，Windows 本机  ")
    lines.append(f"- 方法：每场景顺序采样测延迟分位数；AI 场景额外做 {args.ai_users} 用户并发排队观察  ")
    lines.append("")
    lines.append(Phase.header())
    for phase in phases:
        lines.append("| " + " | ".join(phase.row()) + " |")
    lines.append("")
    report = "\\n".join(lines)

    failed = [p for p in phases if p.failures]
    if failed:
        report += "\\n\\n## 失败明细\\n\\n" + "\\n".join(
            f"- {p.name}: {f}" for p in failed for f in p.failures[:5])
    return report


def _user_id_of(api_base: str, token: str) -> str:
    """从 JWT 解出 sub（仅解 payload，不验签——本机压测用）。"""
    import base64
    payload = token.split(".")[1]
    payload += "=" * (-len(payload) % 4)
    data = json.loads(base64.urlsafe_b64decode(payload))
    return data["sub"]


def main() -> None:
    parser = argparse.ArgumentParser(description="ai-resume 接口基准测试")
    parser.add_argument("--base", default="http://127.0.0.1:8004")
    parser.add_argument("--db", default="resume-backend/.bench/bench.db",
                        help="隔离实例的 SQLite 路径，用于给压测用户发 VIP")
    parser.add_argument("--draft-count", type=int, default=1000)
    parser.add_argument("--samples", type=int, default=30)
    parser.add_argument("--ai-users", type=int, default=5)
    parser.add_argument("--skip-ai", action="store_true")
    parser.add_argument("--out", default="", help="结果 Markdown 追加写入的文件")
    args = parser.parse_args()
    if not Path(args.db).exists():
        print(f"数据库不存在：{args.db}（隔离实例是否已启动？）", file=sys.stderr)
        raise SystemExit(2)
    report = asyncio.run(run(args))
    print(report)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "a", encoding="utf-8") as f:
            f.write("\\n\\n" + report + "\\n")


if __name__ == "__main__":
    main()
