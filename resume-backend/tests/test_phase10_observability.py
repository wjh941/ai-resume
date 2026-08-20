from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_reports_push_mode_and_worker_status(api_client) -> None:
    response = api_client.get("/health")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["push_dispatcher_mode"] == "mock"
    assert data["worker"]["status"] in {"disabled", "unknown", "healthy", "stale"}
    assert "database_type" in data


def test_client_error_and_unhandled_error_are_sanitized_and_structured(api_client, monkeypatch) -> None:
    from app.services import observability

    logged: list[str] = []
    monkeypatch.setattr(observability.logger, "log", lambda _level, message: logged.append(message))
    reported = api_client.post(
        "/api/system/client-errors",
        json={"message": "渲染失败", "component": "resume-editor"},
    )

    @api_client.app.get("/test-phase10-error")
    def raise_for_test():
        raise RuntimeError("internal detail must stay server-side")

    with TestClient(api_client.app, raise_server_exceptions=False) as client:
        client.headers.update(api_client.headers)
        response = client.get("/test-phase10-error")

    assert reported.status_code == 200
    assert response.status_code == 500
    assert "internal detail" not in response.text
    assert any('"request_id"' in message for message in logged)


def test_client_error_route_is_registered_once(api_client) -> None:
    from app.api import system

    routes = [
        route
        for route in system.router.routes
        if getattr(route, "path", None) == "/api/system/client-errors"
        and "POST" in getattr(route, "methods", set())
    ]

    assert len(routes) == 1
