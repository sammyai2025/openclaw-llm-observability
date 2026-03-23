from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from .db import Base, engine, get_db
from .models import LLMCall

Base.metadata.create_all(bind=engine)

app = FastAPI(title="OpenClaw LLM Observability", version="0.1.0")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

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

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.post("/api/v1/llm-calls")
def create_llm_call(payload: LLMCallIn, db: Session = Depends(get_db)):
    row = LLMCall(**payload.model_dump())
    if not row.created_at:
        row.created_at = datetime.utcnow()
    db.add(row)
    db.commit()
    db.refresh(row)
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
