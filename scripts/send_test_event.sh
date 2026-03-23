#!/usr/bin/env bash
set -euo pipefail
BASE_URL="${1:-http://127.0.0.1:8091}"
now=$(date -u +%Y-%m-%dT%H:%M:%SZ)
curl -sS -X POST "$BASE_URL/api/v1/llm-calls" \
  -H 'Content-Type: application/json' \
  --data @- <<JSON
{
  "trace_id": "manual-test-$(date -u +%s)",
  "created_at": "$now",
  "finished_at": "$now",
  "latency_ms": 842,
  "provider": "openai",
  "model": "gpt-5.4",
  "agent_id": "main",
  "session_key": "agent:main:telegram:direct:8324618533",
  "channel": "telegram",
  "chat_id": "telegram:8324618533",
  "user_id": "8324618533",
  "status": "ok",
  "input_tokens": 1820,
  "input_cached_tokens": 640,
  "input_uncached_tokens": 1180,
  "output_tokens": 214,
  "total_tokens": 2034,
  "estimated_cost": 0.0042,
  "prompt_text": "Manual smoke-test prompt for observability verification.",
  "response_text": "Manual smoke-test response stored successfully.",
  "request_json": {"messages": [{"role": "user", "content": "Manual smoke-test prompt for observability verification."}]},
  "response_json": {"id": "resp_manual_test", "finish_reason": "stop"},
  "metadata_json": {"seed": true, "source": "send_test_event.sh"}
}
JSON
printf '\n'
