from __future__ import annotations


PHONE = "13800138000"


def _login_headers(api_client, phone: str = PHONE) -> dict[str, str]:
    response = api_client.post(
        "/api/auth/login-phone",
        json={"phone": phone, "code": "123456"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['data']['token']}"}


def test_demo_phone_login_returns_a_versioned_bearer_token(api_client):
    sent = api_client.post("/api/auth/send-code", json={"phone": PHONE})

    assert sent.status_code == 200
    assert sent.json()["data"]["demo_code"] == "123456"

    login = api_client.post(
        "/api/auth/login-phone",
        json={"phone": PHONE, "code": "123456"},
    )

    assert login.status_code == 200
    assert login.json()["data"]["token"]
    assert login.json()["data"]["user"]["phone"] == PHONE


def test_business_route_rejects_a_missing_bearer_token(api_client):
    response = api_client.get("/api/template/list")

    assert response.status_code == 401


def test_logout_invalidates_the_current_token(api_client):
    headers = _login_headers(api_client)

    assert api_client.get("/api/template/list", headers=headers).status_code == 200
    assert api_client.post("/api/auth/logout", headers=headers).status_code == 200
    assert api_client.get("/api/template/list", headers=headers).status_code == 401
