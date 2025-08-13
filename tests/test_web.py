import os
import importlib

def test_health_endpoint(monkeypatch):
    # Do not set TELEGRAM_BOT_TOKEN so the bot thread won't start in tests
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123")
    # Disable monitor, webhook, and echo for test speed/stability
    monkeypatch.setenv("MONITOR_ENABLED", "false")
    monkeypatch.setenv("ECHO_MODE", "true")
    monkeypatch.delenv("APP_BASE_URL", raising=False)
    monkeypatch.delenv("TELEGRAM_WEBHOOK_SECRET", raising=False)

    # Reload module to apply env
    mod = importlib.import_module("web_jarvis")
    importlib.reload(mod)
    app = mod.flask_app
    client = app.test_client()
    r = client.get("/health")
    assert r.status_code == 200
    js = r.get_json()
    assert js.get("status") == "healthy"


def test_telegram_webhook_ok(monkeypatch):
    # Configure webhook secret and allow-list, but keep token unset to avoid network
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123")
    monkeypatch.setenv("ALLOWED_CHAT_IDS", "123")
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET", "s3cr3t")
    monkeypatch.setenv("ECHO_MODE", "true")
    monkeypatch.setenv("MONITOR_ENABLED", "false")
    mod = importlib.import_module("web_jarvis")
    importlib.reload(mod)
    app = mod.flask_app
    client = app.test_client()
    payload = {"message": {"chat": {"id": 123}, "text": "hello test"}}
    r = client.post("/telegram/s3cr3t", json=payload)
    assert r.status_code == 200
    assert r.get_json().get("ok") is True


