import importlib
import time


def test_chat_webhook_final(monkeypatch):
    # Configure chat auth and webhook secret; don't start Telegram thread
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123")
    monkeypatch.setenv("ALLOWED_CHAT_IDS", "123")
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET", "secret")
    monkeypatch.setenv("MONITOR_ENABLED", "false")
    monkeypatch.setenv("TEST_SYNC", "true")
    monkeypatch.setenv("DISABLE_RETRIEVAL", "true")
    # Bypass preflight and run full DECIDE with stubbed LLM
    monkeypatch.setenv("DISABLE_PREFLIGHT", "true")
    monkeypatch.setenv("ECHO_MODE", "false")

    # Stub LLM decision to be deterministic FINAL
    import main_graph as mg
    importlib.reload(mg)
    monkeypatch.setattr(mg, "call_llm_json", lambda prompt: {"type": "FINAL", "answer": "OK"})

    # Capture Telegram sends
    sent = []
    def _fake_send(text, chat_id=None):
        sent.append((chat_id, text))
        return {"ok": True}

    mod = importlib.import_module("web_jarvis")
    importlib.reload(mod)
    monkeypatch.setattr(mod, "send_telegram_message", _fake_send)

    app = mod.flask_app
    client = app.test_client()
    payload = {"message": {"chat": {"id": 123}, "text": "hello"}}
    r = client.post("/telegram/secret", json=payload)
    assert r.status_code == 200

    # Wait for processing (sync in tests)
    t0 = time.time()
    while len(sent) < 2 and time.time() - t0 < 1.0:
        time.sleep(0.02)
    assert any("Jarvis Complete" in m[1] for m in sent)


def test_chat_status_command(monkeypatch):
    # Basic status reply
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123")
    monkeypatch.setenv("ALLOWED_CHAT_IDS", "123")
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET", "secret")
    monkeypatch.setenv("MONITOR_ENABLED", "false")
    monkeypatch.setenv("DISABLE_PREFLIGHT", "true")
    monkeypatch.setenv("ECHO_MODE", "false")
    monkeypatch.setenv("TEST_SYNC", "true")

    sent = []
    def _fake_send(text, chat_id=None):
        sent.append((chat_id, text))
        return {"ok": True}

    mod = importlib.import_module("web_jarvis")
    importlib.reload(mod)
    monkeypatch.setattr(mod, "send_telegram_message", _fake_send)

    app = mod.flask_app
    client = app.test_client()
    payload = {"message": {"chat": {"id": 123}, "text": "/status"}}
    r = client.post("/telegram/secret", json=payload)
    assert r.status_code == 200
    # Status emits one message synchronously
    assert any("Decisions:" in m[1] for m in sent)


