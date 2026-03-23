#!/usr/bin/env bash
set -euo pipefail
OBS_REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
MODULE_PATH="$OBS_REPO_DIR/instrumentation/openclaw-http-observer.mjs"
OVERRIDE_DIR="$HOME/.config/systemd/user/openclaw-gateway.service.d"
OVERRIDE_FILE="$OVERRIDE_DIR/override.conf"
mkdir -p "$OVERRIDE_DIR"
cat > "$OVERRIDE_FILE" <<EOF
[Service]
Environment=OPENCLAW_LLM_OBS_URL=http://127.0.0.1:8091/api/v1/llm-calls
Environment=OPENCLAW_LLM_OBS_DEBUG_LOG=%h/.openclaw/logs/http-observer.log
Environment=OPENCLAW_LLM_OBS_HOST_HINTS=copilot,openai,anthropic,openrouter,googleapis
Environment=OPENCLAW_LLM_OBS_EXCLUDE_HINTS=127.0.0.1:8091,localhost:8091,discord.com,discordapp.com,api.telegram.org
Environment=NODE_OPTIONS=--import=${MODULE_PATH}
EOF
systemctl --user daemon-reload
systemctl --user restart openclaw-gateway
systemctl --user --no-pager --full status openclaw-gateway | sed -n '1,40p'
echo
echo "Installed gateway HTTP observer. Debug log: $HOME/.openclaw/logs/http-observer.log"
