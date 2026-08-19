from __future__ import annotations


def test_career_task_generate_update_list_and_delete(api_client) -> None:
    generated = api_client.post(
        "/api/career/tasks/generate",
        json={
            "plan_id": "current",
            "action_plan": {
                "seven_day": ["整理作品集"],
                "thirty_day": ["完成一个项目复盘"],
                "ninety_day": [],
            },
        },
    )
    assert generated.status_code == 200, generated.text
    tasks = generated.json()["data"]["items"]
    assert [task["title"] for task in tasks] == ["整理作品集", "完成一个项目复盘"]

    task_id = tasks[0]["id"]
    updated = api_client.patch(
        f"/api/career/tasks/{task_id}",
        json={
            "status": "completed",
            "due_date": "2026-08-30",
            "link_to_application_id": "application-1",
        },
    )
    listed = api_client.get("/api/career/tasks", params={"plan_id": "current"})
    deleted = api_client.delete(f"/api/career/tasks/{task_id}")

    assert updated.status_code == listed.status_code == deleted.status_code == 200
    assert updated.json()["data"]["status"] == "completed"
    assert updated.json()["data"]["due_date"] == "2026-08-30"
    listed_task = next(
        item for item in listed.json()["data"]["items"] if item["id"] == task_id
    )
    assert listed_task["link_to_application_id"] == "application-1"
