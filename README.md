# OpenClaw LLM Observability

Postgres-backed LLM observability service and admin dashboard for OpenClaw-style workloads.

## What this gives you now

- REST ingestion API for every LLM call
- Postgres storage
- browser admin dashboard with filtering
- request/response payload capture
- token + cache usage capture
- latency/error tracking
- OpenClaw-specific metadata fields (agent, session, channel, chat, job)

## Current scope

This repo ships a working observability backend and dashboard.

It does **not** yet patch OpenClaw automatically. Instead, it gives you the service that OpenClaw (or a wrapper around OpenClaw/provider calls) should send traces to.

## Quick start

### Fastest local mode (no Postgres needed)

```bash
cp .env.example .env
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8091
```

### Docker + Postgres mode

```bash
cp .env.example .env
docker compose up --build
```

Then open:
- API health: `http://localhost:8091/healthz`
- Dashboard: `http://localhost:8091/admin`
- API docs: `http://localhost:8091/docs`

## Main endpoint

```text
POST /api/v1/llm-calls
```

## Filtering dashboard

The dashboard supports filtering by:
- provider
- model
- agent id
- session key
- channel
- status
- date window

## Suggested next integration step

Instrument the OpenClaw LLM boundary and POST a normalized trace payload to this service for every model call.

## Experiments

This repo follows experiment-based development.
See `experiments/INDEX.md`.
