# OpenClaw Integration Plan

## Goal

Send one normalized trace to the observability service for every LLM call made by OpenClaw.

## Fields to emit

- provider
- model
- agent_id
- session_key
- channel
- chat_id
- user_id
- job_id
- prompt_text
- response_text
- request_json
- response_json
- input_tokens
- input_cached_tokens
- input_uncached_tokens
- output_tokens
- total_tokens
- latency_ms
- status
- error_type / error_message

## Recommended hook point

Instrument the lowest OpenClaw boundary where:
- provider request payload is finalized
- provider response usage is available
- retries/errors can be observed

## Delivery

POST to:

`POST /api/v1/llm-calls`

## Example payload

```json
{
  "provider": "openai",
  "model": "gpt-5.4",
  "agent_id": "main",
  "session_key": "agent:main:telegram:direct:123",
  "channel": "telegram",
  "status": "ok",
  "latency_ms": 1842,
  "input_tokens": 2871,
  "input_cached_tokens": 1024,
  "input_uncached_tokens": 1847,
  "output_tokens": 311,
  "total_tokens": 3182,
  "prompt_text": "...",
  "response_text": "...",
  "request_json": {"messages": []},
  "response_json": {"id": "resp_..."}
}
```
