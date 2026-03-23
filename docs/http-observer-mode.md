# Gateway HTTP Observer Mode

## Goal

Capture real LLM calls for built-in OpenClaw providers (including GitHub Copilot) by instrumenting the running gateway process at the outbound HTTP layer.

## How it works

- preload a Node module into `openclaw-gateway` with `NODE_OPTIONS=--import=...`
- wrap `globalThis.fetch`
- detect likely LLM provider traffic
- capture request/response bodies, latency, usage, and metadata
- POST normalized traces to the observability service

## Why this exists

This mode is useful when provider proxy routing is not practical because the active provider path is built into OpenClaw and not already going through a configurable HTTP proxy.

## Install

```bash
cd openclaw-llm-observability
chmod +x scripts/install_gateway_http_observer.sh
./scripts/install_gateway_http_observer.sh
```

## Verify

1. Send a real chat message through OpenClaw
2. Check debug log:

```bash
tail -20 ~/.openclaw/logs/http-observer.log
```

3. Check dashboard for a new row

## Caveat

This approach is still more invasive than pure proxy mode, but it is much more stable than patching hashed runtime bundles directly.
