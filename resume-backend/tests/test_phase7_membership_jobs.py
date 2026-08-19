from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import sqlite3

from fastapi.testclient import TestClient


def test_expired_pending_order_cannot_be_fulfilled(api_client):
    order = api_client.post("/api/pay/create-order", json={"package_type": "monthly"}).json()["data"]
    with sqlite3.connect(api_client.app.state.settings.database_path) as connection:
        connection.execute(
            "UPDATE order_record SET create_time = ? WHERE order_id = ?",
            ((datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(), order["order_id"]),
        )

    callback = api_client.post("/api/pay/callback", json={
        "order_id": order["order_id"], "payment_channel": "demo", "payment_status": "paid",
    })

    assert callback.status_code == 409
    assert callback.json()["code"] == "order_expired"
    assert api_client.get("/api/user/order-list").json()["data"]["items"][0]["payment_status"] == "expired"


def test_subscription_persists_match_filter_without_breaking_enabled_field(api_client):
    updated = api_client.put("/api/job-collection/subscription", json={
        "enabled": True, "match_filter": "Shanghai, remote",
    })

    assert updated.status_code == 200
    assert updated.json()["data"] == {
        "enabled": True, "match_filter": "Shanghai, remote", "last_notify_at": None,
    }
    assert api_client.get("/api/job-collection/subscription").json()["data"] == {
        "enabled": True, "match_filter": "Shanghai, remote", "last_notify_at": None,
    }


def test_signed_provider_callback_is_idempotent(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "membership.db"))
    monkeypatch.setenv("TEMP_FILE_PATH", str(tmp_path / "temp"))
    monkeypatch.setenv("AUTH_DEMO_MODE", "true")
    monkeypatch.setenv("JWT_SECRET", "phase7-test-jwt-secret-for-callback")
    monkeypatch.setenv("PAYMENT_CALLBACK_SECRET", "callback-secret")

    from main import create_app

    with TestClient(create_app()) as client:
        login = client.post("/api/auth/login-phone", json={"phone": "13800138008", "code": "123456"})
        client.headers.update({"Authorization": f"Bearer {login.json()['data']['token']}"})
        order = client.post("/api/pay/create-order", json={"package_type": "monthly"}).json()["data"]
        body = f"{order['order_id']}:wechat_pay:paid:provider-transaction-1".encode("utf-8")
        payload = {
            "order_id": order["order_id"],
            "payment_channel": "wechat_pay",
            "payment_status": "paid",
            "provider_transaction_id": "provider-transaction-1",
            "signature": hmac.new(b"callback-secret", body, hashlib.sha256).hexdigest(),
        }
        first = client.post("/api/pay/callback", json=payload)
        second = client.post("/api/pay/callback", json=payload)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["data"]["order"]["entitlement_expire_time"] == second.json()["data"]["order"]["entitlement_expire_time"]
