"""
models/assistant.py — Models for Shadow Assistant + AI call logging
Section: System
Dependencies: ._base.Base
"""

from sqlalchemy import Column, Float, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from ._base import Base


class AssistantLog(Base):
    __tablename__ = "assistant_logs"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    user_message = Column(String)
    assistant_reply = Column(String)
    was_blocked = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AiCallLog(Base):
    """Audit log for every Ollama / Gemini API call.

    Columns
    -------
    provider       : "ollama" | "gemini"
    caller         : module/function that initiated the call (e.g. "ckla_grader.grade_answer")
    prompt_summary : first 200 chars of the prompt (no PII)
    response_summary: first 200 chars of the response
    success        : True if the call returned a usable result
    latency_ms     : round-trip time in milliseconds
    quality_score  : Ollama quality score (0.0–1.0), NULL for Gemini
    fallback_used  : True when Gemini was used as a fallback after Ollama failure/low quality
    error_message  : error string on failure, NULL on success
    created_at     : UTC timestamp
    """

    __tablename__ = "ai_call_log"

    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String(16), nullable=False, index=True)          # "ollama" | "gemini"
    caller = Column(String(120), nullable=False, index=True)           # module.function
    prompt_summary = Column(String(200), nullable=True)                # first 200 chars
    response_summary = Column(String(200), nullable=True)              # first 200 chars
    success = Column(Boolean, nullable=False, default=True)
    latency_ms = Column(Integer, nullable=True)                        # milliseconds
    quality_score = Column(Float, nullable=True)                       # Ollama only
    fallback_used = Column(Boolean, nullable=False, default=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


__all__ = ["AssistantLog", "AiCallLog"]
