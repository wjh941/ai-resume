# -*- coding: utf-8 -*-
"""端到端冒烟测试:登录 -> 建档 -> 推荐 -> 岗位情报 -> 简历草稿 -> Word 导出。"""
import json
import os
import time
import urllib.request

BASE = "http://127.0.0.1:8000"
# 绕过系统代理(Clash 等会劫持 localhost 请求导致挂起)
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def call(method, path, token=None, payload=None, raw=False):
    req = urllib.request.Request(BASE + path, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    t0 = time.perf_counter()
    # AI 已接入真实上游后，岗位情报/职业规划等步骤可能需要 1-2 分钟生成，
    # 可用 SMOKE_TIMEOUT_SECONDS 环境变量覆盖。
    timeout_seconds = int(os.getenv("SMOKE_TIMEOUT_SECONDS", "150"))
    try:
        with OPENER.open(req, data=data, timeout=timeout_seconds) as resp:
            body = resp.read()
            ms = (time.perf_counter() - t0) * 1000
            if raw:
                return resp.headers.get_content_type(), body, ms
            return json.loads(body), ms
    except urllib.error.HTTPError as e:
        ms = (time.perf_counter() - t0) * 1000
        return json.loads(e.read()), ms


ok, _ = call("POST", "/api/auth/send-code", payload={"phone": "13800138000"})
login, _ = call("POST", "/api/auth/login-phone", payload={"phone": "13800138000", "code": "123456"})
token = login["data"]["token"]
print(f"[1] login ok role={login['data']['user']['role']}")

profile, ms = call("POST", "/api/career/profile/save", token, {
    "identity_code": "1", "major": "计算机科学", "education_level": "本科",
    "city_preferences": ["北京"], "industry_preferences": ["互联网"],
    "skills": ["Python", "SQL", "Tableau"]})
print(f"[2] profile/save {ms:.0f}ms code={profile.get('code')}")

rec, ms = call("POST", "/api/career/recommend", token, {
    "identity_code": "1", "major": "计算机科学", "education_level": "本科",
    "city_preferences": ["北京"], "skills": ["Python", "SQL"]})
tiers = rec["data"].get("tiers", {})
flat = [r for group in tiers.values() for r in group][:3]
print(f"[3] career/recommend {ms:.0f}ms tiers={list(tiers.keys())}")
for r in flat:
    print(f"      - {r.get('role', {}).get('role_name')} [{r.get('tier')}] score={r.get('total_score')}")

job, ms = call("POST", "/api/job/query", token, {"role_name": "数据分析师"})
d = job["data"]
print(f"[4] job/query {ms:.0f}ms skills={len(d.get('required_skills', []))} bonus={len(d.get('bonus_skills', []))} route={len(d.get('career_route', []))}")

# /api/job/plan 是 AI 驱动接口：未配置 AI_API_KEY/AI_MODEL 时返回 ai_not_configured（预期行为）。
plan, ms = call("POST", "/api/job/plan", token, {"role_name": "数据分析师", "report_mode": "simplified"})
print(f"[5] job/plan(simplified) {ms:.0f}ms code={plan.get('code')} scope={plan.get('data', {}).get('report_scope', '-') if plan.get('code') == 'ok' else '-'}")

resume = {
    "basic": {"name": "张三", "phone": "13800138000", "email": "zhangsan@example.com", "city": "北京"},
    "job": {"target_role": "数据分析师"},
    "education": [{"school": "某某大学", "major": "计算机科学", "degree": "本科", "start_date": "2021-09", "end_date": "2025-06"}],
    "employment": [],
    "projects": [{"name": "电商用户行为分析", "role": "数据分析", "start_date": "2024-03", "end_date": "2024-06",
                  "description": "使用 Python 分析 100 万条用户行为日志,输出转化漏斗报告"}],
    "skills": {"skills": ["Python", "SQL", "Tableau"], "certificates": []},
    "self_evaluation": "对数据敏感,喜欢用数据驱动决策",
    "section_visibility": {"basic": True, "job": True, "education": True, "employment": True,
                            "projects": True, "skills": True, "self_evaluation": True},
}
# 先清理历史草稿，避免免费额度（vip_required）阻断重复执行
lst0, _ = call("GET", "/api/draft/list", token)
old_items = lst0.get("data") or []
if isinstance(old_items, dict):
    old_items = old_items.get("drafts") or old_items.get("items") or []
for item in old_items:
    if item.get("id"):
        call("DELETE", f"/api/draft/{item['id']}", token)

saved, ms = call("POST", "/api/draft/save", token, {"job_title": "数据分析师", "template_id": "analytics", "resume": resume})
draft_id = (saved.get("data") or {}).get("id") or (saved.get("data") or {}).get("draft_id")
print(f"[6] draft/save {ms:.0f}ms code={saved.get('code')} draft_id={draft_id}")

lst, _ = call("GET", "/api/draft/list", token)
items = lst.get("data") or []
if isinstance(items, dict):
    items = items.get("drafts") or items.get("items") or []
print(f"[7] draft/list count={len(items)}")

if draft_id:
    exp, ms = call("POST", "/api/export/word", token, {"draft_id": draft_id})
    print(f"[8] export/word {ms:.0f}ms code={exp.get('code')}")
    url = (exp.get("data") or {}).get("download_url")
    if url:
        ctype, body, ms = call("GET", url, token, raw=True)
        with open(r"D:\Projects\ai-resume-miniprogram\scripts\_smoke_export.docx", "wb") as f:
            f.write(body)
        print(f"[9] download {ms:.0f}ms type={ctype} bytes={len(body)} -> scripts/_smoke_export.docx")

readiness, ms = call("POST", "/api/resume/readiness", token, {"resume": resume})
r = readiness.get("data") or {}
print(f"[10] resume/readiness {ms:.0f}ms ready={r.get('ready', r.get('is_ready', '-'))} issues={len(r.get('issues', r.get('problems', []) or []))}")
