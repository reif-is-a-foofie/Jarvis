import os
import sys
from typing import List


FATAL = []
WARN = []


def _append_no_proxy(hosts: List[str]) -> None:
    current = os.getenv("NO_PROXY", "")
    parts = [p.strip() for p in current.split(",") if p.strip()]
    for h in hosts:
        if h not in parts:
            parts.append(h)
    os.environ["NO_PROXY"] = ",".join(parts)


def ensure() -> None:
    # Proxy hardening for OpenAI
    _append_no_proxy(["api.openai.com", "openai.com"])

    echo_mode = os.getenv("ECHO_MODE", "false").lower() == "true"
    model = os.getenv("MODEL", "openai:gpt-4o-mini")

    # OpenAI key required unless echo mode or a non-openai model is configured
    if (not echo_mode) and model.startswith("openai:"):
        if not os.getenv("OPENAI_API_KEY"):
            FATAL.append("Missing OPENAI_API_KEY while MODEL uses OpenAI and ECHO_MODE is false")

    # Qdrant external consistency
    q_url = os.getenv("QDRANT_URL", "").strip()
    q_key = os.getenv("QDRANT_API_KEY", "").strip()
    if q_url and not q_key:
        FATAL.append("QDRANT_URL is set but QDRANT_API_KEY is missing")

    # Telegram
    tg_tok = os.getenv("TELEGRAM_BOT_TOKEN")
    tg_chat = os.getenv("TELEGRAM_CHAT_ID")
    if not (tg_tok and tg_chat):
        WARN.append("Telegram not fully configured; bot replies disabled")

    if FATAL:
        msg = "Preflight failed:\n - " + "\n - ".join(FATAL)
        print(msg, file=sys.stderr)
        if os.getenv("DISABLE_PREFLIGHT", "false").lower() != "true":
            sys.exit(1)
    if WARN:
        print("Preflight warnings:\n - " + "\n - ".join(WARN))


