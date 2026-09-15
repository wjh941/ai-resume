from __future__ import annotations

from dataclasses import replace


FEATURE_NAMES = {
    "resume_import",
    "sms_login",
    "wechat_oauth",
    "payment",
    "push_notifications",
    "job_matching",
}


def test_health_exposes_non_sensitive_feature_contract(api_client):
    response = api_client.get("/health")

    assert response.status_code == 200
    data = response.json()["data"]
    assert {"job_plan", "job_match", "ai_setup"} <= set(data["capabilities"])
    assert set(data["features"]) == FEATURE_NAMES
    for feature in data["features"].values():
        assert set(feature) == {"enabled", "mode", "notice"}
        assert feature["mode"] in {"real", "demo", "disabled"}
        assert isinstance(feature["enabled"], bool)
        assert feature["notice"]
    assert "secret" not in response.text.lower()
    assert "api_key" not in response.text.lower()


def test_health_feature_modes_follow_settings_without_exposing_credentials(api_client):
    api_client.app.state.settings = replace(
        api_client.app.state.settings,
        auth_demo_mode=False,
        sms_provider="http",
        sms_http_endpoint="https://sms.example.test",
        sms_access_key="access-key",
        sms_access_secret="access-secret",
        sms_sign_name="sign",
        sms_template_id="template",
        wechat_open_app_id="wx-app",
        wechat_open_app_secret="wx-secret",
        wechat_open_redirect_uri="https://example.test/oauth/callback",
        membership_enabled=True,
        payment_demo_mode=False,
        wechat_pay_mch_id="mch-id",
        wechat_pay_api_v3_key="payment-secret",
        wechat_pay_app_id="wx-pay-app",
        payment_callback_secret="callback-secret",
        push_dispatcher_mode="real",
    )

    data = api_client.get("/health").json()["data"]["features"]

    assert data["resume_import"]["mode"] == "real"
    assert data["sms_login"] == {
        "enabled": True,
        "mode": "real",
        "notice": "已配置短信登录服务。",
    }
    assert data["wechat_oauth"]["mode"] == "disabled"
    assert data["wechat_oauth"]["enabled"] is False
    assert data["payment"]["mode"] == "disabled"
    assert data["push_notifications"]["mode"] == "disabled"
    assert data["job_matching"]["enabled"] is True
    assert "payment-secret" not in api_client.get("/health").text


def test_health_marks_optional_features_disabled_when_unconfigured(api_client):
    api_client.app.state.settings = replace(
        api_client.app.state.settings,
        auth_demo_mode=False,
        sms_provider="disabled",
        wechat_open_app_id="",
        wechat_open_app_secret="",
        wechat_open_redirect_uri="",
        membership_enabled=False,
        payment_demo_mode=False,
        push_dispatcher_mode="mock",
        resume_import_max_file_bytes=0,
    )

    features = api_client.get("/health").json()["data"]["features"]

    for name in ("sms_login", "wechat_oauth", "payment", "push_notifications"):
        assert features[name]["enabled"] is False
        assert features[name]["mode"] == "disabled"
        assert features[name]["notice"]
    assert features["resume_import"]["mode"] == "disabled"


def test_health_requires_complete_http_sms_gateway(api_client):
    api_client.app.state.settings = replace(
        api_client.app.state.settings,
        auth_demo_mode=False,
        sms_provider="aliyun",
        sms_http_endpoint="https://sms.example.test",
        sms_access_key="key",
        sms_access_secret="secret",
        sms_sign_name="sign",
        sms_template_id="template",
    )

    feature = api_client.get("/health").json()["data"]["features"]["sms_login"]
    assert feature["enabled"] is False
    assert feature["mode"] == "disabled"


def test_health_detail_reads_updated_app_settings(api_client):
    api_client.app.state.settings = replace(api_client.app.state.settings, push_dispatcher_mode="real")
    feature = api_client.get("/health/detail").json()["data"]["features"]["push_notifications"]
    assert feature["mode"] == "disabled"


def test_health_does_not_advertise_demo_payment_in_production(api_client):
    api_client.app.state.settings = replace(
        api_client.app.state.settings,
        app_env="production",
        membership_enabled=True,
        payment_demo_mode=True,
    )

    feature = api_client.get("/health").json()["data"]["features"]["payment"]
    assert feature["mode"] == "disabled"
    assert feature["enabled"] is False
