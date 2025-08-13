import os
import json
import requests
import threading
import time
from flask import Flask, request, jsonify
from main_graph import app as jarvis_app, State
from main_graph import ingest as ingest_text

flask_app = Flask(__name__)
METRICS = {"started_at": time.time(), "decisions": 0, "actions": 0, "errors": 0, "last_error": ""}
MONITOR_ENABLED = os.getenv("MONITOR_ENABLED", "false").lower() == "true"
MONITOR_INTERVAL = int(os.getenv("MONITOR_INTERVAL_SEC", "60"))
MONITOR_FAIL_THRESHOLD = int(os.getenv("MONITOR_FAIL_THRESHOLD", "2"))
_monitor_fail_count = 0

# Telegram Bot Configuration and Auth
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
ALLOWED_CHAT_IDS = set(filter(None, (os.getenv("ALLOWED_CHAT_IDS", "").split(",") if os.getenv("ALLOWED_CHAT_IDS") else [])))
if TELEGRAM_CHAT_ID:
    ALLOWED_CHAT_IDS.add(str(TELEGRAM_CHAT_ID))
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

def send_telegram_message(text, chat_id=None):
    """Send message to Telegram"""
    if not TELEGRAM_TOKEN:
        return {"error": "No Telegram token configured"}
    
    target_chat = chat_id or TELEGRAM_CHAT_ID
    url = f"{TELEGRAM_API_URL}/sendMessage"
    data = {
        "chat_id": target_chat,
        "text": text[:4000],  # Telegram message limit
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=data, timeout=10)
        return response.json()
    except Exception as e:
        print(f"Error sending Telegram message: {e}")
        return {"error": str(e)}

def reset_telegram_webhook():
    if not TELEGRAM_TOKEN:
        return
    try:
        requests.post(
            f"{TELEGRAM_API_URL}/deleteWebhook",
            json={"drop_pending_updates": True},
            timeout=10,
        )
        print("🔧 Telegram webhook cleared; using long polling.")
    except Exception as e:
        print(f"Error clearing Telegram webhook: {e}")

def ensure_webhook_if_configured():
    if not TELEGRAM_TOKEN:
        return False

def _monitor_loop():
    global _monitor_fail_count
    print("🩺 Monitor loop starting...")
    while True:
        try:
            r = requests.get("http://127.0.0.1:" + str(int(os.environ.get("PORT", 5000))) + "/health", timeout=10)
            ok = r.ok and r.json().get("status") == "healthy"
            if ok:
                _monitor_fail_count = 0
                METRICS["monitor_last_ok"] = time.time()
            else:
                _monitor_fail_count += 1
        except Exception as e:
            _monitor_fail_count += 1
            METRICS["last_error"] = f"monitor: {e}"
        if _monitor_fail_count >= MONITOR_FAIL_THRESHOLD:
            try:
                send_telegram_message("⚠️ Health check failing consecutively. Investigate deployment.", TELEGRAM_CHAT_ID)
                _monitor_fail_count = 0
            except Exception:
                pass
        time.sleep(MONITOR_INTERVAL)
    secret = os.getenv("TELEGRAM_WEBHOOK_SECRET", "").strip()
    base = os.getenv("APP_BASE_URL", "").strip()
    if not secret or not base:
        return False
    try:
        url = f"{base.rstrip('/')}/telegram/{secret}"
        set_url = f"{TELEGRAM_API_URL}/setWebhook"
        r = requests.post(set_url, json={"url": url, "drop_pending_updates": True}, timeout=10)
        ok = r.ok and r.json().get("ok", False)
        print(f"🌐 Telegram webhook {'set' if ok else 'failed'}: {url}")
        return ok
    except Exception as e:
        print(f"Error setting Telegram webhook: {e}")
        return False

def process_jarvis_goal(goal, chat_id):
    """Process goal through Jarvis and send result via Telegram"""
    try:
        # Send acknowledgment
        send_telegram_message(f"🤖 *Jarvis Processing:* {goal}", chat_id)
        # Ingest user message for memory (thread-scoped)
        try:
            ingest_text(f"user[{chat_id}]: {goal}", src="chat-user")
        except Exception:
            pass
        
        # Execute through Jarvis LangGraph
        state = State(goal=goal, context=[], decision={}, log=[])
        # Provide a checkpointer thread_id using the Telegram chat as the thread key
        result = jarvis_app.invoke(
            state,
            config={"configurable": {"thread_id": str(chat_id), "checkpoint_ns": "telegram"}}
        )
        
        # Format response
        decision = result.get("decision", {})
        decision_type = decision.get("type", "UNKNOWN")
        
        if decision_type == "FINAL":
            answer = decision.get("answer", "Task completed")
            response = f"✅ *Jarvis Complete*\n\n{answer}"
        elif decision_type == "ACT":
            tool = decision.get("tool", "unknown")
            response = f"⚡ *Jarvis Action:* {tool}\n\nExecuting your request..."
        else:
            response = f"🔄 *Jarvis Status:* {decision_type}\n\nProcessing your goal..."
        
        # Add log info if available
        logs = result.get("log", [])
        if logs:
            response += f"\n\n📋 *Actions taken:* {len(logs)}"
        
        # Update metrics and send result back to Telegram
        METRICS["decisions"] += 1
        if logs:
            METRICS["actions"] += len(logs)
        send_telegram_message(response, chat_id)
        # Ingest assistant answer for memory (thread-scoped)
        try:
            if decision_type == "FINAL":
                ingest_text(f"assistant[{chat_id}]: {decision.get('answer','')}\nctx: {state.get('context',[])}", src="chat-assistant")
        except Exception:
            pass
        
    except Exception as e:
        error_msg = f"❌ *Error processing goal:*\n{str(e)}"
        METRICS["errors"] += 1
        METRICS["last_error"] = str(e)
        send_telegram_message(error_msg, chat_id)

def get_telegram_updates(offset: int | None = None, timeout_seconds: int = 50):
    """Get new messages from Telegram"""
    if not TELEGRAM_TOKEN:
        return []
    
    try:
        url = f"{TELEGRAM_API_URL}/getUpdates"
        params = {"timeout": timeout_seconds}
        if offset is not None:
            params["offset"] = offset
        response = requests.get(url, params=params, timeout=timeout_seconds + 5)
        data = response.json()
        return data.get("result", [])
    except Exception as e:
        print(f"Error getting Telegram updates: {e}")
        return []

def telegram_bot_polling():
    """Poll Telegram for new messages"""
    print("🤖 Jarvis Telegram bot starting...")
    # If webhook configured, skip polling
    if ensure_webhook_if_configured():
        print("📡 Webhook configured; skipping long polling.")
        return
    reset_telegram_webhook()
    offset: int | None = None
    
    while True:
        try:
            updates = get_telegram_updates(offset=offset, timeout_seconds=50)
            
            last_update_id: int | None = None
            for update in updates:
                update_id = update.get("update_id", 0)
                last_update_id = update_id
                message = update.get("message", {})
                chat = message.get("chat", {})
                chat_id = str(chat.get("id", ""))
                text = message.get("text", "")
                
                # Only respond to messages from authorized chat(s)
                if (chat_id in ALLOWED_CHAT_IDS) and text:
                    cmd = text.strip()
                    if cmd.startswith("/start"):
                        send_telegram_message("Welcome. Use /goal <text> to set a goal.", chat_id)
                        continue
                    if cmd.startswith("/help"):
                        send_telegram_message("Commands: /goal <text>, /status, /cancel", chat_id)
                        continue
                    if cmd.startswith("/status"):
                        send_telegram_message(f"Decisions: {METRICS['decisions']}, Actions: {METRICS['actions']}, Errors: {METRICS['errors']}", chat_id)
                        continue
                    if cmd.startswith("/goal "):
                        cmd = cmd[len("/goal "):].strip()
                    # Process in background thread
                    print(f"📨 Received goal: {cmd}")
                    threading.Thread(
                        target=process_jarvis_goal,
                        args=(cmd, chat_id),
                        daemon=True
                    ).start()
            if last_update_id is not None:
                offset = last_update_id + 1
            
            time.sleep(2)  # Poll every 2 seconds
            
        except Exception as e:
            print(f"Error in bot polling: {e}")
            time.sleep(5)

# Start Telegram bot in background
if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
    bot_thread = threading.Thread(target=telegram_bot_polling, daemon=True)
    bot_thread.start()
    print("🚀 Jarvis Telegram bot started!")
    # One-time boot notification (natural language)
    try:
        send_telegram_message("I am awake and listening. How can I serve you today?", TELEGRAM_CHAT_ID)
    except Exception:
        pass
    # Optional health monitor
    if MONITOR_ENABLED:
        threading.Thread(target=_monitor_loop, daemon=True).start()

# Minimal web server for Heroku health checks and (optional) Telegram webhook
@flask_app.route('/')
def home():
    return "🤖 Jarvis is running! Chat with me on Telegram."

@flask_app.route('/telegram/<token>', methods=['POST'])
def telegram_webhook(token: str):
    secret = os.getenv("TELEGRAM_WEBHOOK_SECRET", "")
    if not secret or token != secret:
        return jsonify({"ok": False}), 403
    try:
        update = request.get_json(force=True, silent=True) or {}
        message = update.get("message", {})
        chat = message.get("chat", {})
        chat_id = str(chat.get("id", ""))
        text = message.get("text", "")
        if (chat_id in ALLOWED_CHAT_IDS) and text:
            threading.Thread(target=process_jarvis_goal, args=(text, chat_id), daemon=True).start()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@flask_app.route('/health')
def health():
    return jsonify({
        "status": "healthy", 
        "service": "jarvis-telegram-bot",
        "telegram_configured": bool(TELEGRAM_TOKEN and TELEGRAM_CHAT_ID),
        "metrics": METRICS
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🌐 Starting web server on port {port}")
    flask_app.run(host="0.0.0.0", port=port, debug=False)