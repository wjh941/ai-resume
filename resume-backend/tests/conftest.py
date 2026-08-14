from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import sys


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


@pytest.fixture
def api_client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "resume_demo.db"))
    monkeypatch.setenv("TEMP_FILE_PATH", str(tmp_path / "temp"))
    monkeypatch.setenv("AUTH_DEMO_MODE", "true")
    monkeypatch.setenv("JWT_SECRET", "test-jwt-secret-for-authentication")

    from main import create_app

    with TestClient(create_app()) as client:
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
