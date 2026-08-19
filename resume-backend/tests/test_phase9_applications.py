from __future__ import annotations


def _application_payload(**changes) -> dict:
    payload = {
        "role_name": "数据工程师",
        "company": "示例公司",
        "city": "上海",
        "source": "官网",
        "status": "interview",
        "contact_info": "张老师 13800000000",
        "attachment_ref": "材料.zip",
        "next_interview_at": "2026-08-25T10:00:00+00:00",
    }
    payload.update(changes)
    return payload


def test_application_timeline_reminder_and_interview_date_filter(api_client) -> None:
    created = api_client.post("/api/applications", json=_application_payload())
    assert created.status_code == 200, created.text
    application = created.json()["data"]
    assert application["contact_info"] == "张老师 13800000000"
    assert application["attachment_ref"] == "材料.zip"

    event = api_client.post(
        f"/api/applications/{application['id']}/timeline",
        json={
            "title": "一面",
            "description": "记录面试重点",
            "occurred_at": "2026-08-20T10:00:00+00:00",
        },
    )
    reminder = api_client.post(
        f"/api/applications/{application['id']}/reminders",
        json={"reminder_at": "2026-08-25T09:30:00+00:00"},
    )
    timeline = api_client.get(f"/api/applications/{application['id']}/timeline")
    filtered = api_client.get("/api/applications?interview_date=2026-08-25")

    assert event.status_code == reminder.status_code == timeline.status_code == filtered.status_code == 200
    assert timeline.json()["data"]["items"][0]["title"] == "一面"
    assert filtered.json()["data"]["items"][0]["id"] == application["id"]


def test_application_timeline_is_scoped_to_current_user(api_client, auth_headers) -> None:
    application = api_client.post("/api/applications", json=_application_payload()).json()["data"]
    api_client.post(
        f"/api/applications/{application['id']}/timeline",
        json={"title": "一面", "occurred_at": "2026-08-20T10:00:00+00:00"},
    )
    other_headers = auth_headers("13900139000")

    owner_response = api_client.get(f"/api/applications/{application['id']}/timeline")
    other_response = api_client.get(
        f"/api/applications/{application['id']}/timeline", headers=other_headers
    )

    assert owner_response.status_code == 200
    assert other_response.status_code == 404
