# 🔐 Security Guidelines for Jarvis

## API Key Management

### ❌ NEVER commit API keys to git
- The `.env` file is gitignored to prevent accidental commits
- Use placeholder values in documentation and scripts
- Real credentials should only exist in environment variables

### ✅ Secure Practices

1. **Local Development:**
   ```bash
   # Use the setup script
   ./setup_env.sh
   
   # Or manually create .env file
   cp .env.example .env
   # Edit .env with your real credentials
   ```

2. **Heroku Deployment:**
   ```bash
   # Set environment variables first
   export OPENAI_API_KEY="your_real_key"
   export TELEGRAM_BOT_TOKEN="your_real_token"
   export TELEGRAM_CHAT_ID="your_real_chat_id"
   
   # Then deploy
   ./deploy.sh
   ```

3. **Production Environment:**
   - Use Heroku's config vars (never hardcode)
   - Rotate keys regularly
   - Monitor API usage for anomalies

## Files Containing Credentials

### Safe (Committed to Git):
- `.env.example` - Template with placeholders
- `deploy_instructions.md` - Contains placeholder examples
- `deploy.sh` - Uses environment variables

### Private (Not Committed):
- `.env` - Real credentials (gitignored)
- Any local scripts with real keys

## Emergency Response

If credentials are accidentally committed:
1. **Immediately rotate all affected API keys**
2. **Force push to remove from git history**
3. **Update all deployment environments**

## Manifesto Compliance

Per the manifesto guardrails:
- No wildcard env secrets
- Protect privacy as sacred
- Every security decision must increase freedom and safety