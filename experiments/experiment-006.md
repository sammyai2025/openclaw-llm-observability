# Experiment 006

- Date: 2026-03-23 21:28 UTC
- Repo: openclaw-llm-observability
- Prompt: "is there no simpler and better way to do this. I just need to record all the LLM calls ... yes please do so. and lets just do it. make it happen"
- Summary: Pivot from brittle OpenClaw runtime patching to a cleaner provider-proxy approach that records all calls at the network boundary.

## Changes

- Added OpenAI-compatible proxy routes for `/v1/chat/completions` and `/v1/responses`
- Added Anthropic proxy route for `/v1/messages`
- Added upstream base URL and API key environment settings
- Added request/response/usage extraction on the proxy path
- Added proxy mode documentation

## Outcome

The observability service can now act as the actual capture point for LLM traffic, which is simpler and more reliable than patching OpenClaw internals.
