# -*- coding: utf-8 -*-
"""ai-resume Locust 压测场景（标准工具形态，便于评审者复现）。

与 bench_api.py 的分工：
- bench_api.py：顺序采样测延迟分位数（P50/P95/P99），产出 README 用数据。
- 本文件：用 Locust 模拟持续多用户负载，观察吞吐与错误率，可生成 HTML 报告。

前置：用 start-bench-backend.ps1 启动隔离实例（限流已调高）。

安装与运行：
  pip install locust
  locust -f scripts/benchmarks/locustfile.py --host http://127.0.0.1:8004 --headless -u 20 -r 5 -t 1m --html .bench/locust-report.html

场景说明：
- 每个虚拟用户先完成演示验证码登录拿到 JWT，再循环执行读多写少的真实混合负载。
- AI 接口（job/query 未命中缓存、ai-rewrite）默认低权重：真实模型调用又贵又慢，
  压测目的是验证限流与降级路径，不是把上游模型打挂。
"""

from __future__ import annotations

import random

from locust import HttpUser, between, task

DEMO_CODE = "123456"
ROLES = ["数据分析师", "前端开发工程师", "产品经理", "算法工程师"]


class ResumeUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self) -> None:
        self.phone = f"1392{random.randint(0, 9999999):07d}"
        self.client.post("/api/auth/send-code", json={"phone": self.phone},
                         name="/api/auth/send-code")
        resp = self.client.post("/api/auth/login-phone",
                                json={"phone": self.phone, "code": DEMO_CODE},
                                name="/api/auth/login-phone")
        token = ""
        if resp.status_code == 200:
            token = resp.json()["data"]["token"]
        self.client.headers["Authorization"] = f"Bearer {token}"

    @task(6)
    def list_drafts(self) -> None:
        self.client.get("/api/draft/list", name="/api/draft/list")

    @task(4)
    def job_match(self) -> None:
        self.client.post("/api/job/match",
                         json={"target_role": random.choice(ROLES),
                               "report_mode": "simplified"},
                         name="/api/job/match")

    @task(3)
    def career_recommend(self) -> None:
        self.client.post("/api/career/recommend",
                         json={"identity_code": "1", "major": "计算机科学",
                               "education_level": "本科", "city_preferences": ["北京"],
                               "skills": ["Python", "SQL"]},
                         name="/api/career/recommend")

    @task(2)
    def readiness(self) -> None:
        self.client.post("/api/resume/readiness",
                         json={"resume": _minimal_resume()},
                         name="/api/resume/readiness")

    @task(1)
    def save_draft(self) -> None:
        self.client.post("/api/draft/save",
                         json={"client_id": "locust", "job_title": "数据分析师",
                               "template_id": "analytics",
                               "resume": _minimal_resume()},
                         name="/api/draft/save")


def _minimal_resume() -> dict:
    return {
        "version": 1,
        "basic": {"name": "压测用户", "phone": "13920000000",
                  "email": "locust@example.com", "city": "北京"},
        "job": {"target_role": "数据分析师"},
        "education": [], "employment": [], "projects": [],
        "skills": {"skills": ["Python", "SQL"], "certificates": []},
        "self_evaluation": "",
        "section_visibility": {"basic": True, "job": True, "education": True,
                               "employment": True, "projects": True,
                               "skills": True, "self_evaluation": True},
    }
