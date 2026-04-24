"""
routers/ai_assistant.py — Floating AI Assistant (Shadow) for interactive chat & voice (V2)
Section: System / AI
Dependencies: httpx, Ollama (local), ENV[GEMINI_API_KEY] (fallback)
API:
  POST /api/assistant/chat
  GET  /api/assistant/health
  GET  /api/assistant/settings
  POST /api/assistant/settings
  GET  /api/assistant/logs
"""

import os
import logging
from typing import Optional, List

import httpx
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from datetime import datetime, timezone

try:
    from backend.database import get_db
except ImportError:
    from ..database import get_db

try:
    from backend.auth import get_current_child
except ImportError:
    def get_current_child(): return {"id": 1, "username": "gia"}

from sqlalchemy.orm import Session
from pydantic import BaseModel

try:
    from backend.models.system import AppConfig
except ImportError:
    from ..models.system import AppConfig

from backend.models.assistant import AssistantLog

from .ai_assistant_safety import (
    SYSTEM_PROMPT_INJECTION_DEFENSE,
    validate_input,
    validate_output,
    mask_pii,
    GEMINI_SAFETY_SETTINGS
)
from .ai_assistant_log import get_assistant_usage, async_log_chat

# Default Shadow settings
SHADOW_DEFAULTS = {
    "shadow_gia_name":        "Gia",
    "shadow_gia_age":         "9",
    "shadow_gia_school":      "international school",
    "shadow_gia_interests":   "reading, math, drawing",
    "shadow_daily_limit":     "30",
    "shadow_session_minutes": "15",
    "shadow_blocked_topics":  "",
    "shadow_enabled":         "true",
}

def _get_cfg(db: Session, key: str) -> str:
    row = db.query(AppConfig).filter(AppConfig.key == key).first()
    return row.value if row else SHADOW_DEFAULTS.get(key, "")

def _set_cfg(db: Session, key: str, value: str):
    row = db.query(AppConfig).filter(AppConfig.key == key).first()
    now = datetime.now(timezone.utc).isoformat()
    if row:
        row.value = value
        row.updated_at = now
    else:
        db.add(AppConfig(key=key, value=value, updated_at=now))
    db.commit()

router = APIRouter()
logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "gemma2:2b")

class ChatHistoryItem(BaseModel):
    role: str
    content: str

class AssistantChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatHistoryItem]] = []
    session_id: str
    context: Optional[dict] = None

def _build_system_prompt(db: Session | None = None) -> str:
    """Build persona from DB settings (falls back to defaults)."""
    def cfg(key: str) -> str:
        return _get_cfg(db, key) if db else SHADOW_DEFAULTS.get(key, "")

    name       = cfg("shadow_gia_name")
    age        = cfg("shadow_gia_age")
    school     = cfg("shadow_gia_school")
    interests  = cfg("shadow_gia_interests")
    blocked    = cfg("shadow_blocked_topics").strip()

    extra_blocked = f"- Never discuss: {blocked}.\n" if blocked else ""

    return (
        f"Your name is Shadow. You are {name}'s study buddy.\n"
        f"{name} is {age} years old, a native English speaker at a {school}.\n"
        f"She is smart and curious. Her interests include: {interests}.\n"
        "[Tone]\n"
        "- Talk like a cool older friend, not a teacher.\n"
        "- Short, clear, natural English — like texting a friend.\n"
        "- No emojis. No bullet points. No long explanations.\n"
        "[Rules]\n"
        "- 1-2 sentences MAX. If you need more, use 3 short sentences.\n"
        "- If she asks about a word, give the meaning + one example sentence.\n"
        "- If she asks a math question, walk through it simply step by step.\n"
        "- Never respond to violence, profanity, or off-topic requests.\n"
        "- Always respond in English only.\n"
        f"{extra_blocked}"
        f"{SYSTEM_PROMPT_INJECTION_DEFENSE}"
    )

async def _call_ollama(messages: list) -> str | None:
    """Call local Ollama. Returns reply text or None on failure."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{OLLAMA_URL}/api/chat",
                json={"model": OLLAMA_MODEL, "messages": messages, "stream": False}
            )
            if resp.status_code == 200:
                return resp.json().get("message", {}).get("content", "").strip() or None
    except Exception as e:
        logger.warning(f"Ollama call failed: {e}")
    return None


async def _call_gemini(history_payload: list) -> str | None:
    """Call Gemini API. Returns reply text or None on failure."""
    if not GEMINI_API_KEY:
        return None
    try:
        gemini_url = "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent"
        payload = {
            "system_instruction": {"parts": [{"text": _build_system_prompt()}]},
            "contents": history_payload,
            "safetySettings": [
                {"category": k, "threshold": v} for k, v in GEMINI_SAFETY_SETTINGS.items()
            ],
            "generationConfig": {"maxOutputTokens": 300}
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                gemini_url, json=payload, headers={"x-goog-api-key": GEMINI_API_KEY}
            )
            if resp.status_code == 200:
                candidates = resp.json().get("candidates", [])
                if candidates:
                    text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
                    return text or None
    except Exception as e:
        logger.error(f"Gemini call failed: {e}")
    return None


@router.get("/api/assistant/health")
async def health_check():
    """Health check for Observability requirements."""
    ollama_ok = False
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(f"{OLLAMA_URL}/api/tags")
            ollama_ok = r.status_code == 200
    except Exception:
        pass
    return {
        "ollama": "ok" if ollama_ok else "unavailable",
        "gemini": "ok" if GEMINI_API_KEY else "missing",
        "db": "ok"
    }

@router.post("/api/assistant/chat")
async def assistant_chat(
    req: AssistantChatRequest, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    child = Depends(get_current_child)
):
    """Handle chat message with 2-pass safety logic, PII masking, and usage limits."""
    # 0. Check Usage Limit
    usage = get_assistant_usage(db, child)
    if usage["remaining"] <= 0:
        raise HTTPException(status_code=429, detail="LimitExceeded")

    # 1. Validation & Masking
    raw_message = req.message.strip()
    if not raw_message:
        raise HTTPException(status_code=400, detail="Empty request")
        
    safe_message = mask_pii(raw_message[:200])  # Enforce 200 char limit
    
    is_safe, fallback_reply = validate_input(safe_message)
    if not is_safe:
        background_tasks.add_task(async_log_chat, db, req.session_id, safe_message, fallback_reply, True)
        return {
            "reply": fallback_reply, 
            "session_id": req.session_id, 
            "turn_count": len(req.history) // 2 + 1,
            "remaining_today": usage["remaining"] - 1
        }

    # 2. Build message history (Ollama format)
    pruned_history = req.history[-10:] if req.history else []
    system_prompt = _build_system_prompt(db)
    if req.context:
        ctx_parts = []
        if req.context.get("lesson"):
            ctx_parts.append(f"Lesson: {req.context['lesson']}")
        if req.context.get("activity"):
            ctx_parts.append(f"Activity: {req.context['activity']}")
        if ctx_parts:
            system_prompt += "\n[Current Activity]\n" + "\n".join(ctx_parts) + "\n"
    ollama_messages = [{"role": "system", "content": system_prompt}]
    for h in pruned_history:
        ollama_messages.append({"role": h.role, "content": h.content})
    ollama_messages.append({"role": "user", "content": safe_message})

    # Gemini format (fallback)
    gemini_history = []
    for h in pruned_history:
        role = "user" if h.role == "user" else "model"
        gemini_history.append({"role": role, "parts": [{"text": h.content}]})
    gemini_history.append({"role": "user", "parts": [{"text": safe_message}]})

    # 3. Ollama → Gemini fallback
    final_reply = "Shadow doesn't know how to answer that! Can you ask again?"
    text = await _call_ollama(ollama_messages)
    if not text:
        logger.info("Ollama unavailable, falling back to Gemini")
        text = await _call_gemini(gemini_history)
    if text:
        final_reply = validate_output(text)

    # 4. Background log and respond
    background_tasks.add_task(async_log_chat, db, req.session_id, safe_message, final_reply, False)

    return {
        "reply": final_reply,
        "session_id": req.session_id,
        "turn_count": len(pruned_history) // 2 + 1,
        "remaining_today": usage["remaining"] - 1
    }


class ShadowSettings(BaseModel):
    shadow_gia_name:        str = "Gia"
    shadow_gia_age:         str = "9"
    shadow_gia_school:      str = "international school"
    shadow_gia_interests:   str = "reading, math, drawing"
    shadow_daily_limit:     str = "30"
    shadow_session_minutes: str = "15"
    shadow_blocked_topics:  str = ""
    shadow_enabled:         str = "true"


@router.get("/api/assistant/settings")
def get_shadow_settings(db: Session = Depends(get_db)):
    """Return current Shadow settings."""
    return {k: _get_cfg(db, k) for k in SHADOW_DEFAULTS}


@router.post("/api/assistant/settings")
def save_shadow_settings(body: ShadowSettings, db: Session = Depends(get_db)):
    """Save Shadow settings to AppConfig."""
    for key, value in body.model_dump().items():
        _set_cfg(db, key, str(value).strip())
    return {"ok": True}


@router.get("/api/assistant/logs")
def get_shadow_logs(limit: int = 50, db: Session = Depends(get_db)):
    """Return recent Shadow chat logs for parent review."""
    from sqlalchemy import desc
    logs = (
        db.query(AssistantLog)
        .order_by(desc(AssistantLog.created_at))
        .limit(min(limit, 200))
        .all()
    )
    return [
        {
            "id": l.id,
            "session_id": l.session_id,
            "user_message": l.user_message,
            "assistant_reply": l.assistant_reply,
            "was_blocked": l.was_blocked,
            "created_at": str(l.created_at),
        }
        for l in logs
    ]
