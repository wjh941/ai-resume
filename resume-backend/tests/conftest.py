from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient
from pathlib import Path
from datetime import datetime, timedelta, timezone
import sqlite3
import sys


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# 测试封闭性：禁止 load_settings() 读取开发者本地 .env（其中可能包含
# 非默认 JWT_SECRET、PRODUCTION=false 等），否则生产加固断言会假失败。
# conftest 先于测试模块导入执行，因此此处在任何 app 导入前生效。
os.environ.setdefault("RESUME_SKIP_DOTENV", "1")


@pytest.fixture
def api_client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "resume_demo.db"))
    monkeypatch.setenv("TEMP_FILE_PATH", str(tmp_path / "temp"))
    monkeypatch.setenv("AUTH_DEMO_MODE", "true")
    monkeypatch.setenv("JWT_SECRET", "test-jwt-secret-for-authentication")
    monkeypatch.setenv("AI_PROVIDER", "openai_compatible")
    monkeypatch.setenv("AI_API_KEY", "")
    monkeypatch.setenv("AI_MODEL", "")

    from main import create_app
    from test_support import TestAIClient

    with TestClient(create_app()) as client:
        client.app.state.ai_client = TestAIClient()
        # 既有业务测试默认以同一演示用户调用；鉴权测试会显式移除该请求头。
        login = client.post(
            "/api/auth/login-phone",
            json={"phone": "13800138000", "code": "123456"},
        )
        assert login.status_code == 200
        client.headers.update({"Authorization": f"Bearer {login.json()['data']['token']}"})
        yield client


@pytest.fixture
def auth_headers(api_client):
    def create(phone: str = "13800138000") -> dict[str, str]:
        response = api_client.post(
            "/api/auth/login-phone",
            json={"phone": phone, "code": "123456"},
        )
        assert response.status_code == 200
        return {"Authorization": f"Bearer {response.json()['data']['token']}"}

    return create


def grant_vip(api_client, level: str = "premium", days: int = 365) -> None:
    """测试夹具：显式配置当前 JWT 用户的会员状态，不绕过业务路由的鉴权。"""
    token = api_client.headers["Authorization"].split(" ", 1)[1]
    user_id = api_client.app.state.auth_service.verify(token)
    now = datetime.now(timezone.utc)
    with sqlite3.connect(api_client.app.state.settings.database_path) as connection:
        connection.execute(
            """
            INSERT INTO user_vip (user_id, vip_level, expire_time, auto_renew, create_time)
            VALUES (?, ?, ?, 0, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                vip_level = excluded.vip_level,
                expire_time = excluded.expire_time,
                auto_renew = 0
            """,
            (user_id, level, (now + timedelta(days=days)).isoformat(), now.isoformat()),
        )


def operator_headers(api_client) -> dict[str, str]:
    """测试夹具：把当前登录用户提升为 operator 并重签 Token，模拟白名单运营账号。"""
    token = api_client.headers["Authorization"].split(" ", 1)[1]
    user_id = api_client.app.state.auth_service.verify(token)
    with sqlite3.connect(api_client.app.state.settings.database_path) as connection:
        connection.execute("UPDATE users SET role = 'operator' WHERE user_id = ?", (user_id,))
    user = api_client.app.state.user_repository.get(user_id)
    return {"Authorization": f"Bearer {api_client.app.state.auth_service.issue_token(user)}"}


def make_resume_payload() -> dict:
    return {
        "version": 1,
        "basic": {
            "name": "Zhang San",
            "phone": "13800138000",
            "email": "zhang@example.com",
            "city": "Beijing",
        },
        "job": {
            "target_role": "Data Engineer",
            "employment_type": "full_time",
            "expected_salary": "20k-30k",
        },
        "education": [
            {
                "school": "Example University",
                "major": "Computer Science",
                "degree": "Bachelor",
                "start_date": "2018-09",
                "end_date": "2022-06",
                "courses": "",
            }
        ],
        "employment": [
            {
                "company": "Example Company",
                "position": "Data Analyst",
                "start_date": "2022-07",
                "end_date": "2024-01",
                "description": "Built reporting pipelines.",
            }
        ],
        "projects": [
            {
                "name": "Analytics Platform",
                "role": "Contributor",
                "start_date": "2023-01",
                "end_date": "2023-12",
                "description": "Delivered a reporting workflow.",
            }
        ],
        "skills": {"skills": ["Python", "SQL"], "certificates": []},
        "self_evaluation": "Reliable and detail-oriented.",
        "section_visibility": {
            "basic": True,
            "job": True,
            "education": True,
            "employment": True,
            "projects": True,
            "skills": True,
            "self_evaluation": True,
        },
    }


def make_draft_payload(client_id: str = "demo-client", **changes) -> dict:
    payload = {
        "client_id": client_id,
        "job_title": "Data Engineer",
        "template_id": "technology",
        "resume": make_resume_payload(),
    }
    payload.update(changes)
    return payload
