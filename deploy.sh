#!/bin/bash

echo "🤖 Deploying Jarvis to Heroku..."

# Check if required environment variables are set
if [ -z "$OPENAI_API_KEY" ] || [ -z "$TELEGRAM_BOT_TOKEN" ] || [ -z "$TELEGRAM_CHAT_ID" ]; then
    echo "❌ Error: Required environment variables not set!"
    echo "Please set the following environment variables before running this script:"
    echo "export OPENAI_API_KEY='your_openai_api_key'"
    echo "export TELEGRAM_BOT_TOKEN='your_telegram_bot_token'"
    echo "export TELEGRAM_CHAT_ID='your_telegram_chat_id'"
    exit 1
fi

# Set the stack to container
echo "📦 Setting Heroku stack to container..."
heroku stack:set container -a definitely-not-jarvis

# Set environment variables
echo "🔧 Setting environment variables..."
heroku config:set OPENAI_API_KEY="$OPENAI_API_KEY" -a definitely-not-jarvis
heroku config:set TELEGRAM_BOT_TOKEN="$TELEGRAM_BOT_TOKEN" -a definitely-not-jarvis
heroku config:set TELEGRAM_CHAT_ID="$TELEGRAM_CHAT_ID" -a definitely-not-jarvis
heroku config:set MODEL="openai:gpt-4o-mini" -a definitely-not-jarvis

# Deploy
echo "🚀 Deploying to Heroku..."
git push heroku main

# Scale if needed
echo "⚡ Scaling web dyno..."
heroku ps:scale web=1 -a definitely-not-jarvis

echo "✅ Deployment complete!"
echo "📊 Check status: heroku ps -a definitely-not-jarvis"
echo "📝 View logs: heroku logs --tail -a definitely-not-jarvis"