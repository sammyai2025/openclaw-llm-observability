# Experiment 007

- Date: 2026-03-23 21:40 UTC
- Repo: openclaw-llm-observability
- Prompt: "The right place is the Node HTTP/fetch layer inside the running OpenClaw gateway process ... proceed"
- Summary: Add a gateway preload module that instruments outbound HTTP/fetch at the Node process layer so built-in provider traffic like GitHub Copilot can be observed without patching hashed runtime bundles.

## Changes

- Added `instrumentation/openclaw-http-observer.mjs`
- Added `scripts/install_gateway_http_observer.sh`
- Added `docs/http-observer-mode.md`
- Captures request/response bodies, latency, usage, and writes a debug log
- Posts normalized traces to the observability collector

## Outcome

This gives a stable interception point for built-in provider traffic and is a better fit for the current VM-native GitHub Copilot setup than bundle patching.
