# Experiments Index

- 001 — 2026-03-23 18:30 UTC — Create initial Postgres-backed observability service and admin dashboard for OpenClaw LLM call tracing
- 002 — 2026-03-23 18:41 UTC — Add SQLite fallback so the service can run fast on a VM without Docker/Postgres
- 003 — 2026-03-23 18:43 UTC — Seed the dashboard with test traces and add a repeatable manual emitter for verification
- 004 — 2026-03-23 20:24 UTC — Run the observability app as a persistent user systemd service so port 8091 stays up
- 005 — 2026-03-23 20:48 UTC — Add direct OpenClaw runtime patcher to emit real traces at the LLM output boundary
- 006 — 2026-03-23 21:28 UTC — Pivot to provider-proxy mode so LLM call capture happens at the network boundary
