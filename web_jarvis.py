import os
import json
import requests
import threading
import time
from flask import Flask, request, jsonify
from main_graph import app as jarvis_app, State

flask_app = Flask(__name__)

# Telegram Bot Configuration
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
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

def process_jarvis_goal(goal, chat_id):
    """Process goal through Jarvis and send result via Telegram"""
    try:
        # Send acknowledgment
        send_telegram_message(f"🤖 *Jarvis Processing:* {goal}", chat_id)
        
        # Execute through Jarvis LangGraph
        state = State(goal=goal, context=[], decision={}, log=[])
        result = jarvis_app.invoke(state)
        
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
        
        # Send result back to Telegram
        send_telegram_message(response, chat_id)
        
    except Exception as e:
        error_msg = f"❌ *Error processing goal:*\n{str(e)}"
        send_telegram_message(error_msg, chat_id)

def get_telegram_updates():
    """Get new messages from Telegram"""
    if not TELEGRAM_TOKEN:
        return []
    
    try:
        url = f"{TELEGRAM_API_URL}/getUpdates"
        response = requests.get(url, timeout=10)
        data = response.json()
        return data.get("result", [])
    except Exception as e:
        print(f"Error getting Telegram updates: {e}")
        return []

def telegram_bot_polling():
    """Poll Telegram for new messages"""
    print("🤖 Jarvis Telegram bot starting...")
    offset = 0
    
    while True:
        try:
            updates = get_telegram_updates()
            
            for update in updates:
                update_id = update.get("update_id", 0)
                if update_id <= offset:
                    continue
                    
                offset = update_id
                message = update.get("message", {})
                chat = message.get("chat", {})
                chat_id = str(chat.get("id", ""))
                text = message.get("text", "")
                
                # Only respond to messages from authorized chat
                if chat_id == TELEGRAM_CHAT_ID and text:
                    print(f"📨 Received goal: {text}")
                    # Process in background thread
                    threading.Thread(
                        target=process_jarvis_goal,
                        args=(text, chat_id),
                        daemon=True
                    ).start()
            
            time.sleep(2)  # Poll every 2 seconds
            
        except Exception as e:
            print(f"Error in bot polling: {e}")
            time.sleep(5)

# Start Telegram bot in background
if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
    bot_thread = threading.Thread(target=telegram_bot_polling, daemon=True)
    bot_thread.start()
    print("🚀 Jarvis Telegram bot started!")

# Minimal web server for Heroku health checks
@flask_app.route('/')
def home():
    return "🤖 Jarvis is running! Chat with me on Telegram."

@flask_app.route('/health')
def health():
    return jsonify({
        "status": "healthy", 
        "service": "jarvis-telegram-bot",
        "telegram_configured": bool(TELEGRAM_TOKEN and TELEGRAM_CHAT_ID)
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🌐 Starting web server on port {port}")
    flask_app.run(host="0.0.0.0", port=port, debug=False)