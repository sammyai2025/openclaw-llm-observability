# Experiment 002

- Date: 2026-03-23 18:41 UTC
- Repo: openclaw-llm-observability
- Prompt: "can i access these over public ip ... i tried the urls and could not access them"
- Summary: Add a SQLite fallback mode so the observability service can be started immediately on the VM without Docker or Postgres.

## Changes

- Changed default database URL to SQLite for quick local bring-up
- Kept Postgres as an optional configuration path
- Updated README quick-start instructions to include the no-Postgres path
- Added experiment tracking for this fallback mode

## Outcome

The service can be brought up quickly on a bare VM and made reachable for immediate testing, without waiting on Docker or Postgres.
