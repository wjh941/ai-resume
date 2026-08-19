from __future__ import annotations

from io import BytesIO
import json
import zipfile

from conftest import make_draft_payload


def test_production_sms_service_sends_a_gateway_code_and_rejects_reuse(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("AUTH_DEMO_MODE", "false")
    monkeypatch.setenv("SMS_PROVIDER", "http")
    monkeypatch.setenv("SMS_HTTP_ENDPOINT", "https://sms.example.test/send")
    monkeypatch.setenv("SMS_ACCESS_KEY", "access-key")
    monkeypatch.setenv("SMS_ACCESS_SECRET", "access-secret")
    monkeypatch.setenv("SMS_SIGN_NAME", "Resume Demo")
    monkeypatch.setenv("SMS_TEMPLATE_ID", "SMS_123")

    from app.config import load_settings
    from app.services.sms import SmsService, VerificationCodeError

    sent: list[tuple[str, dict[str, str], dict[str, str]]] = []
    service = SmsService(
        load_settings(),
        code_factory=lambda: "654321",
        transport=lambda url, headers, payload: sent.append((url, headers, payload)),
    )

    assert service.send_code("13800138000").demo_code is None
    assert sent == [(
        "https://sms.example.test/send",
        {"Authorization": "Bearer access-secret", "X-SMS-Access-Key": "access-key"},
        {
            "phone": "13800138000",
            "code": "654321",
            "sign_name": "Resume Demo",
            "template_id": "SMS_123",
        },
    )]
    service.verify_code("13800138000", "654321")
    try:
        service.verify_code("13800138000", "654321")
    except VerificationCodeError:
        pass
    else:
        raise AssertionError("a consumed verification code must be rejected")


def test_account_export_is_a_zip_and_deletion_anonymizes_owned_data(api_client):
    draft = api_client.post("/api/draft/save", json=make_draft_payload()).json()["data"]
    profile = {
        "identity_code": "2",
        "major": "Computer Science",
        "education_level": "Bachelor",
        "graduation_year": 2027,
        "city_preferences": ["Shanghai"],
        "minimum_salary": "10k",
        "industry_preferences": ["Internet"],
        "work_types": ["full-time"],
        "skills": ["Python"],
    }
    assert api_client.post("/api/career/profile/save", json=profile).status_code == 200
    assert api_client.post("/api/applications", json={
        "company": "Example Co", "role_name": "Data Engineer", "city": "Shanghai",
        "source": "manual", "status": "saved", "interview_notes": "", "notes": "Follow up",
    }).status_code == 200

    export_request = api_client.post("/api/account/data-export")
    assert export_request.status_code == 200
    assert export_request.json()["data"]["status"] == "ready"
    archive = api_client.get(export_request.json()["data"]["download_url"])
    assert archive.status_code == 200
    with zipfile.ZipFile(BytesIO(archive.content)) as bundle:
        exported = json.loads(bundle.read("account-data.json"))
    assert exported["resume_drafts"][0]["id"] == draft["id"]
    assert exported["career_profile"]["major"] == "Computer Science"
    assert exported["applications"][0]["company"] == "Example Co"

    deleted = api_client.post("/api/account/deletion-request")
    assert deleted.status_code == 200
    assert deleted.json()["data"]["status"] == "deleted"
    assert api_client.get("/api/draft/list").status_code == 401

    import sqlite3
    with sqlite3.connect(api_client.app.state.settings.database_path) as connection:
        user = connection.execute("SELECT phone, is_deleted, deleted_at FROM users").fetchone()
        deleted_draft = connection.execute("SELECT user_id, payload_json FROM user_draft").fetchone()
        deleted_profile = connection.execute("SELECT user_id FROM career_profile").fetchone()
    assert user[0].startswith("deleted:")
    assert user[1] == 1 and user[2]
    assert deleted_draft[0] is None and deleted_draft[1] == "{}"
    assert deleted_profile[0] is None
