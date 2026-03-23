# Proxy Mode

## Goal

Capture all LLM calls by routing provider traffic through this observability service instead of patching OpenClaw internals.

## Implemented routes

- `POST /proxy/openai/v1/chat/completions`
- `POST /proxy/openai/v1/responses`
- `POST /proxy/anthropic/v1/messages`

## What gets stored

For every proxied call:
- provider
- model
- prompt text
- response text
- raw request JSON
- raw response JSON
- token usage
- cache token fields where exposed
- latency
- status / error

## How to use

Configure OpenClaw/provider clients to call this service instead of the upstream directly.

Examples:
- OpenAI-compatible clients -> `http://YOUR_SERVER_IP:8091/proxy/openai`
- Anthropic messages -> `http://YOUR_SERVER_IP:8091/proxy/anthropic`

## Auth behavior

The proxy will use upstream API keys from environment variables if configured.
If not configured, it forwards incoming auth headers to the upstream provider.

## Why this is better than patching internals

- stable network boundary
- simpler to reason about
- captures every call routed through it
- independent of OpenClaw internal bundle layout
