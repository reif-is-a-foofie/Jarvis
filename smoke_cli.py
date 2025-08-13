import os
import sys
import json
import time
import argparse
from typing import Dict, Any

import requests


def print_result(name: str, ok: bool, detail: str = "") -> None:
    status = "PASS" if ok else "FAIL"
    line = f"[{status}] {name}"
    if detail:
        line += f" — {detail}"
    print(line)


def test_openai() -> bool:
    try:
        from openai import OpenAI
        # If proxies are set by env, the SDK will use them
        cli = OpenAI()
        _ = cli.chat.completions.create(
            model=os.getenv("MODEL", "gpt-4o-mini").split(":", 1)[-1],
            messages=[{"role": "user", "content": "ping"}],
            temperature=0.0,
        )
        print_result("openai", True)
        return True
    except Exception as e:
        print_result("openai", False, str(e))
        return False


def test_qdrant() -> bool:
    try:
        from qdrant_client import QdrantClient
        url = os.getenv("QDRANT_URL", "").strip()
        key = os.getenv("QDRANT_API_KEY", "").strip() or None
        if url:
            q = QdrantClient(url=url, api_key=key, prefer_grpc=False)
        else:
            q = QdrantClient(":memory:")
        _ = q.get_collections()
        print_result("qdrant", True, "external" if url else "in-memory")
        return True
    except Exception as e:
        print_result("qdrant", False, str(e))
        return False


def test_graph() -> bool:
    try:
        from main_graph import app as jarvis_app
        state: Dict[str, Any] = {"goal": "smoke test: say hello", "context": [], "decision": {}, "log": []}
        out = jarvis_app.invoke(state, config={"configurable": {"thread_id": "smoke-cli"}})
        dtype = out.get("decision", {}).get("type", "?")
        print_result("graph", True, f"decision={dtype}")
        return True
    except Exception as e:
        print_result("graph", False, str(e))
        return False


def test_health() -> bool:
    try:
        base = os.getenv("APP_BASE_URL", "").rstrip("/")
        port = os.getenv("PORT")
        if base:
            url = f"{base}/health"
        elif port:
            url = f"http://127.0.0.1:{port}/health"
        else:
            url = "http://127.0.0.1:5000/health"
        r = requests.get(url, timeout=10)
        ok = r.ok and r.json().get("status") == "healthy"
        print_result("health", ok, url)
        return ok
    except Exception as e:
        print_result("health", False, str(e))
        return False


def test_webhook() -> bool:
    try:
        base = os.getenv("APP_BASE_URL", "").rstrip("/")
        secret = os.getenv("TELEGRAM_WEBHOOK_SECRET", "")
        chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
        if not (base and secret and chat_id):
            print_result("webhook", False, "missing APP_BASE_URL/SECRET/CHAT_ID")
            return False
        url = f"{base}/telegram/{secret}"
        payload = {
            "update_id": int(time.time()),
            "message": {"chat": {"id": int(chat_id)}, "text": "smoke from CLI"},
        }
        r = requests.post(url, json=payload, timeout=10)
        ok = r.ok and r.json().get("ok") is True
        print_result("webhook", ok, url)
        return ok
    except Exception as e:
        print_result("webhook", False, str(e))
        return False


def test_telegram_send() -> bool:
    try:
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        if not (token and chat_id):
            print_result("telegram_send", False, "missing TELEGRAM_* env")
            return False
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        r = requests.post(url, json={"chat_id": chat_id, "text": "smoke: hello"}, timeout=10)
        ok = r.ok and r.json().get("ok") is True
        print_result("telegram_send", ok)
        return ok
    except Exception as e:
        print_result("telegram_send", False, str(e))
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Jarvis smoke tests")
    parser.add_argument("--all", action="store_true", help="run all tests")
    parser.add_argument("--openai", action="store_true")
    parser.add_argument("--qdrant", action="store_true")
    parser.add_argument("--graph", action="store_true")
    parser.add_argument("--health", action="store_true")
    parser.add_argument("--webhook", action="store_true")
    parser.add_argument("--telegram", action="store_true", help="send test message")
    args = parser.parse_args()

    ran_any = False
    ok_all = True
    def run(flag: bool, fn):
        nonlocal ran_any, ok_all
        if flag or args.all:
            ran_any = True
            ok = fn()
            ok_all = ok_all and ok

    run(args.openai, test_openai)
    run(args.qdrant, test_qdrant)
    run(args.graph, test_graph)
    run(args.health, test_health)
    run(args.webhook, test_webhook)
    run(args.telegram, test_telegram_send)

    if not ran_any:
        parser.print_help()
        sys.exit(2)
    sys.exit(0 if ok_all else 1)


if __name__ == "__main__":
    main()


