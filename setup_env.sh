#!/bin/bash

echo "🔐 Jarvis Environment Setup"
echo "=========================="

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ Created .env file from template"
fi

echo ""
echo "Please provide your API credentials:"

# OpenAI API Key
read -p "🔑 Enter your OpenAI API Key: " -s openai_key
echo ""

# Telegram Bot Token  
read -p "🤖 Enter your Telegram Bot Token: " -s telegram_token
echo ""

# Telegram Chat ID
read -p "💬 Enter your Telegram Chat ID: " telegram_chat_id
echo ""

# Update .env file
cat > .env << EOF
MODEL=openai:gpt-4o-mini
OPENAI_API_KEY=$openai_key
TELEGRAM_BOT_TOKEN=$telegram_token
TELEGRAM_CHAT_ID=$telegram_chat_id
EOF

echo "✅ Environment variables saved to .env file"
echo "🔒 Note: .env file is gitignored for security"

# Export for current session
export OPENAI_API_KEY="$openai_key"
export TELEGRAM_BOT_TOKEN="$telegram_token" 
export TELEGRAM_CHAT_ID="$telegram_chat_id"
export MODEL="openai:gpt-4o-mini"

echo ""
echo "✅ Environment variables exported for current session"
echo "🚀 You can now run: ./deploy.sh"