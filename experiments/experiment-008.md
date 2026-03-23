# Experiment 008

- Date: 2026-03-23 22:00 UTC
- Repo: openclaw-llm-observability
- Prompt: "the agent/session is blank also token counts is zero ... go ahead"
- Summary: Upgrade the gateway HTTP observer to parse GitHub Copilot SSE/event-stream responses so the observability system can extract real output text and usage from live calls.

## Changes

- Added SSE/event-stream parsing to the HTTP observer
- Extracted final response payload from `response.completed`-style events when available
- Extracted output text from streaming delta events
- Used parsed final payload for usage fields and response text instead of storing only a raw event-stream blob
- Added SSE metadata markers into stored rows

## Outcome

Live Copilot calls should now produce more useful response text and may populate token usage fields when those values are present in the response stream.
