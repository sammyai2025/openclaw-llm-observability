# Experiment 003

- Date: 2026-03-23 18:43 UTC
- Repo: openclaw-llm-observability
- Prompt: "i can access each of these urls .. but do not see any data yet ... Can you please do that so that i can see them"
- Summary: Seed the observability dashboard with test traces and add a repeatable manual emitter so the service can be verified visually before OpenClaw auto-instrumentation is added.

## Changes

- Added a small manual emitter script for posting sample traces
- Posted seed traces into the running service so the admin dashboard has visible data

## Outcome

The dashboard can now be verified end-to-end with real stored rows, even before automatic OpenClaw instrumentation is wired in.
