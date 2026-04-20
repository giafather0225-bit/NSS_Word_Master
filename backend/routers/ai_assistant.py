"""
routers/ai_assistant.py — Floating AI Assistant (Shadow) for interactive chat & voice (V2)
Section: System / AI
Dependencies: httpx, ENV[GEMINI_API_KEY]
API:
  POST /api/assistant/chat
  GET /api/assistant/health
"""

import os
import logging
from typing import Optional, List, Dict

import httpx
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks

# Try fallback imports for db and auth
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

from .ai_assistant_safety import (
    SYSTEM_PROMPT_INJECTION_DEFENSE,
    validate_input,
    validate_output,
    mask_pii,
    GEMINI_SAFETY_SETTINGS
)
from .ai_assistant_log import get_assistant_usage, async_log_chat

router = APIRouter()
logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

class ChatHistoryItem(BaseModel):
    role: str
    content: str

class AssistantChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatHistoryItem]] = []
    session_id: str

def _build_system_prompt() -> str:
    """Build the base persona along with the injection defense."""
    return (
        "너의 이름은 섀도우(Shadow)야.\n"
        "지아(GIA)의 하나뿐인 AI 친구이자 다정한 선생님이야.\n"
        "[성격]\n"
        "- 다정하고 밝은 말투를 쓰고 이모지를 즐겨 사용해.\n"
        "- 한국어로 대답하되 영어 단어가 나오면 한국어 설명을 덧붙여줘.\n"
        "[규칙]\n"
        "- 2~3문장 이내로 아주 짧게 대답해.\n"
        "- 어려운 개념은 비유로 쉽게 설명해.\n"
        "- 폭력, 욕설, 무서운 이야기에는 절대 응답하지 마.\n"
        f"{SYSTEM_PROMPT_INJECTION_DEFENSE}"
    )

@router.get("/api/assistant/health")
def health_check():
    """Health check for Observability requirements."""
    return {"gemini": "ok" if GEMINI_API_KEY else "missing", "db": "ok"}

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

    # 2. History pruning (Max 5 turns = 10 messages)
    history_payload = []
    pruned_history = req.history[-10:] if req.history else []
    for h in pruned_history:
        role = "user" if h.role == "user" else "model"
        history_payload.append({"role": role, "parts": [{"text": h.content}]})
        
    # Append current message
    history_payload.append({"role": "user", "parts": [{"text": safe_message}]})

    # 3. Gemini Call
    final_reply = "섀도우가 어떻게 대답해야 할지 모르겠어! 다시 한번 말해줄래?"
    if GEMINI_API_KEY:
        try:
            gemini_url = "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent"
            payload = {
                "system_instruction": {"parts": [{"text": _build_system_prompt()}]},
                "contents": history_payload,
                "safetySettings": [
                    {"category": k, "threshold": v} for k, v in GEMINI_SAFETY_SETTINGS.items()
                ],
                "generationConfig": {
                    "maxOutputTokens": 300  # Token Limit
                }
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    gemini_url, json=payload, headers={"x-goog-api-key": GEMINI_API_KEY}
                )
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
                        if text:
                            final_reply = validate_output(text) # 2nd Pass Filter
        except Exception as e:
            logger.error(f"Gemini Request Failed: {e}")
            final_reply = "앗, 서버가 조금 바쁜 것 같아. 10초 뒤에 다시 시도해봐! ⏰"

    # 4. Background log and respond
    background_tasks.add_task(async_log_chat, db, req.session_id, safe_message, final_reply, False)
    
    return {
        "reply": final_reply, 
        "session_id": req.session_id, 
        "turn_count": len(pruned_history) // 2 + 1,
        "remaining_today": usage["remaining"] - 1
    }
