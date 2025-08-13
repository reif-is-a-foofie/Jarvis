# Jarvis Heroku Deployment Instructions

## 🚀 Your Jarvis system is ready for deployment!

### Step 1: Authenticate with Heroku (if not already done)
```bash
heroku login
```

### Step 2: Set the stack to container
```bash
heroku stack:set container -a definitely-not-jarvis
```

### Step 3: Set environment variables
```bash
heroku config:set OPENAI_API_KEY="your_openai_api_key_here" -a definitely-not-jarvis

heroku config:set TELEGRAM_BOT_TOKEN="your_telegram_bot_token_here" -a definitely-not-jarvis

heroku config:set TELEGRAM_CHAT_ID="your_telegram_chat_id_here" -a definitely-not-jarvis

heroku config:set MODEL="openai:gpt-4o-mini" -a definitely-not-jarvis
```

**Alternative: Use the secure deploy script**
1. First set your environment variables locally:
```bash
export OPENAI_API_KEY="your_openai_api_key_here"
export TELEGRAM_BOT_TOKEN="your_telegram_bot_token_here" 
export TELEGRAM_CHAT_ID="your_telegram_chat_id_here"
```

2. Then run the deploy script:
```bash
./deploy.sh
```

### Step 4: Deploy to Heroku
```bash
git push heroku main
```

### Step 5: Scale the web dyno (if needed)
```bash
heroku ps:scale web=1 -a definitely-not-jarvis
```

### Step 6: View logs
```bash
heroku logs --tail -a definitely-not-jarvis
```

## 🎯 What Jarvis Can Do

Once deployed, your Jarvis will be running and ready to:

1. **Accept CLI goals** through its interactive interface
2. **Execute actions** using these tools:
   - `docs.write` - Create/write files
   - `notify.owner` - Send Telegram notifications
   - `compose.apply` - Infrastructure changes (adapted for Heroku)

3. **Workflow**: PLAN → RETRIEVE → DECIDE → ACT/SELF_UPGRADE → FINAL

4. **Vector search** for context retrieval using embeddings

## 🧪 Testing Your Deployment

Once deployed, you can test by accessing the Heroku app and interacting with the CLI interface.

## 📁 Files Created
- `manifesto.yaml` - Core principles and guardrails
- `main_graph.py` - LangGraph workflow engine  
- `requirements.txt` - Python dependencies
- `Dockerfile` - Container configuration
- `heroku.yml` - Heroku build configuration
- `tools/` - Action tools (docs, compose, notify)
- `.env` - Environment variables (local only)

## ⚡ Key Features
- ✅ LangGraph state machine workflow
- ✅ Vector search with Qdrant (in-memory)
- ✅ OpenAI integration for decision making
- ✅ Telegram bot notifications
- ✅ Manifesto-based guardrails
- ✅ Self-upgrade capabilities
- ✅ Docker containerized for Heroku

Your Jarvis is ready to serve! 🤖✨