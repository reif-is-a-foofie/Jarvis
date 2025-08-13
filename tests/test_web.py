import os
import importlib

def test_health_endpoint(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "x")
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


