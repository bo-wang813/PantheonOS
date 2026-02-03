#!/bin/bash
set -e

echo "========================================="
echo "Pantheon ChatRoom Docker Entrypoint"
echo "========================================="

# Default ID_HASH if not provided
ID_HASH=${ID_HASH:-"default"}

echo "Environment:"
echo "  ID_HASH: ${ID_HASH}"
echo "  PANTHEON_REMOTE_BACKEND: ${PANTHEON_REMOTE_BACKEND}"
echo "  NATS_SERVERS: ${NATS_SERVERS}"
echo "  QDRANT_LOCATION: ${QDRANT_LOCATION}"
echo "  WORKSPACE: $(pwd)"
echo ""

# Wait for NATS server (if NATS_MONITOR_URL is set)
if [ -n "$NATS_MONITOR_URL" ]; then
    echo "Waiting for NATS server at $NATS_MONITOR_URL..."
    timeout 30 bash -c "until curl -sf $NATS_MONITOR_URL/healthz > /dev/null 2>&1; do sleep 1; done" || {
        echo "ERROR: NATS server is not ready"
        exit 1
    }
    echo "✓ NATS is ready"
else
    echo "Skipping NATS health check (NATS_MONITOR_URL not set)"
fi

# Wait for Qdrant server (if QDRANT_HTTP_URL is set)
if [ -n "$QDRANT_HTTP_URL" ]; then
    echo "Waiting for Qdrant server at $QDRANT_HTTP_URL..."
    timeout 30 bash -c "until curl -sf $QDRANT_HTTP_URL/healthz > /dev/null 2>&1; do sleep 1; done" || {
        echo "ERROR: Qdrant server is not ready at $QDRANT_HTTP_URL"
        exit 1
    }
    echo "✓ Qdrant is ready"
else
    echo "Skipping Qdrant health check (QDRANT_HTTP_URL not set)"
fi

echo ""
echo "========================================="
echo "Initializing Workspace"
echo "========================================="

# Initialize workspace structure
mkdir -p /workspace/.pantheon
echo "✓ Ensured .pantheon directory exists"

# Create .env.example template if not exists
if [ ! -f /workspace/.env.example ]; then
    cat > /workspace/.env.example << 'EOF'
# ========================================
# Pantheon API Keys Configuration
# ========================================
#
# This is a template file. Your actual config is in .env
# If you need to reset your configuration, copy this file to .env
#
# After editing .env, click the reload button (🔄) to apply changes without restarting.
# Priority: .env > System defaults > settings.json
#
# ========================================

# OpenAI API Key (GPT-4, GPT-3.5, etc.)
# Uncomment and set your own key to use your OpenAI account
#OPENAI_API_KEY=sk-your-openai-key-here

# Anthropic API Key (Claude models)
# Uncomment and set your own key to use your Anthropic account
#ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here

# Google Gemini API Key
# Uncomment and set your own key to use your Google account
#GEMINI_API_KEY=your-gemini-key-here

# DeepSeek API Key
#DEEPSEEK_API_KEY=your-deepseek-key-here

# ========================================
# Advanced Configuration (Optional)
# ========================================

# Custom LiteLLM endpoint
#LITELLM_BASE_URL=https://your-litellm-proxy.com

# Debug mode
#DEBUG=false

# ========================================
# Notes:
# - If you don't set these keys, system default keys will be used
# - Using default keys will deduct quota from your account
# - After editing .env, click reload (🔄) to apply changes
# - .env is gitignored and won't be committed
# ========================================
EOF
    echo "✓ Created .env.example template"
else
    echo "✓ .env.example already exists"
fi

# Auto-create .env from .env.example if not exists
if [ ! -f /workspace/.env ]; then
    cp /workspace/.env.example /workspace/.env
    echo "✓ Created .env from template (auto-copied from .env.example)"
    echo "  → Edit /workspace/.env to configure your API keys"
    echo "  → Click reload button (🔄) after editing to apply changes"
else
    echo "✓ .env configuration file already exists"
fi

echo ""
echo "========================================="
echo "Starting Pantheon ChatRoom"
echo "========================================="

# Execute the command with ID_HASH parameter
if [ $# -eq 0 ]; then
    # No arguments provided, use default command with ID_HASH
    exec python -m pantheon.chatroom --id_hash="${ID_HASH}"
else
    # Arguments provided, pass them to pantheon.chatroom with ID_HASH
    # This ensures ID_HASH is always used for stable service_id generation
    exec python -m pantheon.chatroom --id_hash="${ID_HASH}" "$@"
fi
