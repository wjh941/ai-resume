from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_public_compose_keeps_third_party_services_disabled_or_mocked():
    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")

    assert compose.count("restart: unless-stopped") >= 2
    assert 'AUTH_DEMO_MODE: "false"' in compose
    assert "SMS_PROVIDER: disabled" in compose
    assert 'PAYMENT_DEMO_MODE: "false"' in compose
    assert "PUSH_DISPATCHER_MODE: mock" in compose
    assert "http://127.0.0.1:8000/health" in compose
    assert "os.kill(1, 0)" in compose
    assert compose.count("condition: service_healthy") >= 2


def test_deployment_precheck_explains_public_safety_and_qualification():
    precheck = (ROOT / "docs" / "DEPLOYMENT_PRECHECK.md").read_text(encoding="utf-8")

    assert "PRODUCTION=true" in precheck
    assert "OpenAPI" in precheck
    assert "账号密码" in precheck
    assert "商业短信" in precheck
    assert "微信支付" in precheck
    assert "订阅消息" in precheck
