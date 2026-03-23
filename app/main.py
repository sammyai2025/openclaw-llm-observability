import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import httpx
from fastapi import Depends, FastAPI, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from .db import Base, engine, get_db
from .models import LLMCall

Base.metadata.create_all(bind=engine)

app = FastAPI(title="OpenClaw LLM Observability", version="0.2.0")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

OPENAI_UPSTREAM_BASE_URL = os.getenv("OPENAI_UPSTREAM_BASE_URL", "https://api.openai.com")
OPENAI_UPSTREAM_API_KEY = os.getenv("OPENAI_UPSTREAM_API_KEY", "")
ANTHROPIC_UPSTREAM_BASE_URL = os.getenv("ANTHROPIC_UPSTREAM_BASE_URL", "https://api.anthropic.com")
ANTHROPIC_UPSTREAM_API_KEY = os.getenv("ANTHROPIC_UPSTREAM_API_KEY", "")
REQUEST_TIMEOUT_SECONDS = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "180"))

class LLMCallIn(BaseModel):
    trace_id: Optional[str] = None
    parent_trace_id: Optional[str] = None
    created_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    latency_ms: Optional[int] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    agent_id: Optional[str] = None
    session_key: Optional[str] = None
    channel: Optional[str] = None
    chat_id: Optional[str] = None
    user_id: Optional[str] = None
    job_id: Optional[str] = None
    status: Optional[str] = Field(default="ok")
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    input_tokens: Optional[int] = None
    input_cached_tokens: Optional[int] = None
    input_uncached_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    reasoning_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    estimated_cost: Optional[float] = None
    prompt_text: Optional[str] = None
    response_text: Optional[str] = None
    request_json: Optional[dict] = None
    response_json: Optional[dict] = None
    metadata_json: Optional[dict] = None


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def first_nonempty(*values):
    for value in values:
        if value is not None and value != "":
            return value
    return None


def extract_openai_prompt_text(body: dict[str, Any]) -> str | None:
    if isinstance(body.get("input"), str):
        return body["input"]
    if isinstance(body.get("input"), list):
        return str(body["input"])
    messages = body.get("messages") or []
    parts: list[str] = []
    if isinstance(messages, list):
        for msg in messages:
            if not isinstance(msg, dict):
                continue
            content = msg.get("content")
            if isinstance(content, str):
                parts.append(content)
            elif isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and isinstance(item.get("text"), str):
                        parts.append(item["text"])
    return "\n\n".join(parts).strip() or None


def extract_openai_response_text(body: dict[str, Any]) -> str | None:
    outputs: list[str] = []
    if isinstance(body.get("output_text"), str):
        return body["output_text"]
    if isinstance(body.get("output"), list):
        for item in body["output"]:
            if not isinstance(item, dict):
                continue
            content = item.get("content")
            if isinstance(content, list):
                for piece in content:
                    if isinstance(piece, dict) and isinstance(piece.get("text"), str):
                        outputs.append(piece["text"])
    choices = body.get("choices") or []
    if isinstance(choices, list):
        for ch in choices:
            if not isinstance(ch, dict):
                continue
            msg = ch.get("message") or {}
            if isinstance(msg, dict) and isinstance(msg.get("content"), str):
                outputs.append(msg["content"])
    return "\n\n".join(outputs).strip() or None


def parse_openai_usage(body: dict[str, Any]) -> dict[str, int | None]:
    usage = body.get("usage") or {}
    input_tokens = first_nonempty(usage.get("input_tokens"), usage.get("prompt_tokens"))
    output_tokens = first_nonempty(usage.get("output_tokens"), usage.get("completion_tokens"))
    total_tokens = usage.get("total_tokens")
    cached = None
    details = usage.get("input_tokens_details") or usage.get("prompt_tokens_details") or {}
    if isinstance(details, dict):
        cached = first_nonempty(details.get("cached_tokens"), details.get("cache_read_tokens"))
    uncached = None
    if input_tokens is not None and cached is not None:
        try:
            uncached = max(0, int(input_tokens) - int(cached))
        except Exception:
            uncached = None
    reasoning = None
    out_details = usage.get("output_tokens_details") or {}
    if isinstance(out_details, dict):
        reasoning = first_nonempty(out_details.get("reasoning_tokens"), out_details.get("reasoning"))
    return {
        "input_tokens": int(input_tokens) if input_tokens is not None else None,
        "input_cached_tokens": int(cached) if cached is not None else None,
        "input_uncached_tokens": int(uncached) if uncached is not None else None,
        "output_tokens": int(output_tokens) if output_tokens is not None else None,
        "reasoning_tokens": int(reasoning) if reasoning is not None else None,
        "total_tokens": int(total_tokens) if total_tokens is not None else None,
    }


def extract_anthropic_prompt_text(body: dict[str, Any]) -> str | None:
    messages = body.get("messages") or []
    parts: list[str] = []
    if isinstance(messages, list):
        for msg in messages:
            if not isinstance(msg, dict):
                continue
            content = msg.get("content")
            if isinstance(content, str):
                parts.append(content)
            elif isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and isinstance(item.get("text"), str):
                        parts.append(item["text"])
    return "\n\n".join(parts).strip() or None


def extract_anthropic_response_text(body: dict[str, Any]) -> str | None:
    content = body.get("content") or []
    parts: list[str] = []
    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
    return "\n\n".join(parts).strip() or None


def parse_anthropic_usage(body: dict[str, Any]) -> dict[str, int | None]:
    usage = body.get("usage") or {}
    input_tokens = usage.get("input_tokens")
    output_tokens = usage.get("output_tokens")
    cache_read = usage.get("cache_read_input_tokens")
    cache_write = usage.get("cache_creation_input_tokens")
    total = None
    if input_tokens is not None and output_tokens is not None:
        total = int(input_tokens) + int(output_tokens)
    uncached = None
    if input_tokens is not None and cache_read is not None:
        uncached = max(0, int(input_tokens) - int(cache_read))
    return {
        "input_tokens": int(input_tokens) if input_tokens is not None else None,
        "input_cached_tokens": int(cache_read) if cache_read is not None else int(cache_write) if cache_write is not None else None,
        "input_uncached_tokens": int(uncached) if uncached is not None else None,
        "output_tokens": int(output_tokens) if output_tokens is not None else None,
        "reasoning_tokens": None,
        "total_tokens": total,
    }


def store_call(db: Session, payload: dict[str, Any]) -> LLMCall:
    row = LLMCall(**payload)
    if not row.created_at:
        row.created_at = utcnow()
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


async def forward_json(method: str, url: str, headers: dict[str, str], body: dict[str, Any]) -> tuple[int, dict[str, Any], float]:
    started = utcnow()
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
        resp = await client.request(method, url, headers=headers, json=body)
    finished = utcnow()
    latency_ms = (finished - started).total_seconds() * 1000.0
    try:
        data = resp.json()
    except Exception:
        data = {"raw_text": resp.text}
    return resp.status_code, data, latency_ms


@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.post("/api/v1/llm-calls")
def create_llm_call(payload: LLMCallIn, db: Session = Depends(get_db)):
    row = store_call(db, payload.model_dump())
    return {"id": row.id, "status": "stored"}


@app.get("/api/v1/llm-calls")
def list_llm_calls(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    agent_id: Optional[str] = None,
    session_key: Optional[str] = None,
    channel: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
):
    q = select(LLMCall).order_by(desc(LLMCall.created_at)).limit(limit)
    if provider:
        q = q.where(LLMCall.provider == provider)
    if model:
        q = q.where(LLMCall.model == model)
    if agent_id:
        q = q.where(LLMCall.agent_id == agent_id)
    if session_key:
        q = q.where(LLMCall.session_key == session_key)
    if channel:
        q = q.where(LLMCall.channel == channel)
    if status:
        q = q.where(LLMCall.status == status)
    rows = db.execute(q).scalars().all()
    return rows


@app.post("/proxy/openai/v1/chat/completions")
async def proxy_openai_chat_completions(request: Request, db: Session = Depends(get_db)):
    body = await request.json()
    incoming_auth = request.headers.get("authorization", "")
    upstream_auth = f"Bearer {OPENAI_UPSTREAM_API_KEY}" if OPENAI_UPSTREAM_API_KEY else incoming_auth
    headers = {"Authorization": upstream_auth, "Content-Type": "application/json"}
    status_code, data, latency_ms = await forward_json("POST", f"{OPENAI_UPSTREAM_BASE_URL.rstrip('/')}/v1/chat/completions", headers, body)
    usage = parse_openai_usage(data)
    store_call(db, {
        "trace_id": data.get("id"),
        "created_at": utcnow(),
        "finished_at": utcnow(),
        "latency_ms": int(latency_ms),
        "provider": "openai",
        "model": first_nonempty(data.get("model"), body.get("model")),
        "status": "ok" if status_code < 400 else "error",
        "error_type": None if status_code < 400 else f"http_{status_code}",
        "error_message": None if status_code < 400 else str(data)[:1000],
        "prompt_text": extract_openai_prompt_text(body),
        "response_text": extract_openai_response_text(data),
        "request_json": body,
        "response_json": data,
        "metadata_json": {"proxy_route": "openai_chat_completions"},
        **usage,
    })
    return JSONResponse(status_code=status_code, content=data)


@app.post("/proxy/openai/v1/responses")
async def proxy_openai_responses(request: Request, db: Session = Depends(get_db)):
    body = await request.json()
    incoming_auth = request.headers.get("authorization", "")
    upstream_auth = f"Bearer {OPENAI_UPSTREAM_API_KEY}" if OPENAI_UPSTREAM_API_KEY else incoming_auth
    headers = {"Authorization": upstream_auth, "Content-Type": "application/json"}
    status_code, data, latency_ms = await forward_json("POST", f"{OPENAI_UPSTREAM_BASE_URL.rstrip('/')}/v1/responses", headers, body)
    usage = parse_openai_usage(data)
    store_call(db, {
        "trace_id": data.get("id"),
        "created_at": utcnow(),
        "finished_at": utcnow(),
        "latency_ms": int(latency_ms),
        "provider": "openai",
        "model": first_nonempty(data.get("model"), body.get("model")),
        "status": "ok" if status_code < 400 else "error",
        "error_type": None if status_code < 400 else f"http_{status_code}",
        "error_message": None if status_code < 400 else str(data)[:1000],
        "prompt_text": extract_openai_prompt_text(body),
        "response_text": extract_openai_response_text(data),
        "request_json": body,
        "response_json": data,
        "metadata_json": {"proxy_route": "openai_responses"},
        **usage,
    })
    return JSONResponse(status_code=status_code, content=data)


@app.post("/proxy/anthropic/v1/messages")
async def proxy_anthropic_messages(request: Request, db: Session = Depends(get_db)):
    body = await request.json()
    incoming_auth = request.headers.get("x-api-key", "")
    upstream_key = ANTHROPIC_UPSTREAM_API_KEY or incoming_auth
    headers = {
        "x-api-key": upstream_key,
        "anthropic-version": request.headers.get("anthropic-version", "2023-06-01"),
        "content-type": "application/json",
    }
    status_code, data, latency_ms = await forward_json("POST", f"{ANTHROPIC_UPSTREAM_BASE_URL.rstrip('/')}/v1/messages", headers, body)
    usage = parse_anthropic_usage(data)
    store_call(db, {
        "trace_id": data.get("id"),
        "created_at": utcnow(),
        "finished_at": utcnow(),
        "latency_ms": int(latency_ms),
        "provider": "anthropic",
        "model": first_nonempty(data.get("model"), body.get("model")),
        "status": "ok" if status_code < 400 else "error",
        "error_type": None if status_code < 400 else f"http_{status_code}",
        "error_message": None if status_code < 400 else str(data)[:1000],
        "prompt_text": extract_anthropic_prompt_text(body),
        "response_text": extract_anthropic_response_text(data),
        "request_json": body,
        "response_json": data,
        "metadata_json": {"proxy_route": "anthropic_messages"},
        **usage,
    })
    return JSONResponse(status_code=status_code, content=data)


@app.get("/admin", response_class=HTMLResponse)
def admin_dashboard(
    request: Request,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    agent_id: Optional[str] = None,
    channel: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = select(LLMCall).order_by(desc(LLMCall.created_at)).limit(250)
    if provider:
        q = q.where(LLMCall.provider == provider)
    if model:
        q = q.where(LLMCall.model == model)
    if agent_id:
        q = q.where(LLMCall.agent_id == agent_id)
    if channel:
        q = q.where(LLMCall.channel == channel)
    if status:
        q = q.where(LLMCall.status == status)
    rows = db.execute(q).scalars().all()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "rows": rows,
            "filters": {
                "provider": provider or "",
                "model": model or "",
                "agent_id": agent_id or "",
                "channel": channel or "",
                "status": status or "",
            },
        },
    )
