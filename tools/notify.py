import os, requests
def run(args):
    token=os.getenv("TELEGRAM_BOT_TOKEN"); chat=os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat: return {"error":"missing_telegram_env"}
    r=requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                   json={"chat_id": chat, "text": args["text"][:4000],
                         "parse_mode": args.get("parse_mode","Markdown")},
                   timeout=10)
    return {"ok": r.ok, "status": r.status_code, "body": r.text[:200]}