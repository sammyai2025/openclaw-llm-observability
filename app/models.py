from datetime import datetime
from sqlalchemy import DateTime, Float, Integer, JSON, Text, String
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base

class LLMCall(Base):
    __tablename__ = "llm_calls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trace_id: Mapped[str | None] = mapped_column(String(128), index=True)
    parent_trace_id: Mapped[str | None] = mapped_column(String(128), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    provider: Mapped[str | None] = mapped_column(String(64), index=True)
    model: Mapped[str | None] = mapped_column(String(128), index=True)
    agent_id: Mapped[str | None] = mapped_column(String(128), index=True)
    session_key: Mapped[str | None] = mapped_column(String(255), index=True)
    channel: Mapped[str | None] = mapped_column(String(64), index=True)
    chat_id: Mapped[str | None] = mapped_column(String(255), index=True)
    user_id: Mapped[str | None] = mapped_column(String(255), index=True)
    job_id: Mapped[str | None] = mapped_column(String(128), index=True)
    status: Mapped[str | None] = mapped_column(String(32), index=True)
    error_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    input_cached_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    input_uncached_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reasoning_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estimated_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    prompt_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    response_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    request_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    response_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
