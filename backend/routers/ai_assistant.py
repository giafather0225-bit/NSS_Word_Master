"""
routers/ai_assistant.py — Floating AI Assistant (Shadow) for interactive chat & voice
Section: Shared
Dependencies: httpx, ENV[GEMINI_API_KEY]
API:
  POST /api/assistant/chat
"""

import os
import logging
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
OLLAMA_MODEL = "gemma2:2b"

class AssistantChatRequest(BaseModel):
    message: str
    context: Optional[str] = None  # Future proofing to send current lesson or game stage

def _build_system_prompt(user_message: str, context: Optional[str]) -> str:
    """Build the prompt instructing Gemini to act as Shadow."""
    context_str = f"Current context: {context}\n" if context else ""
    return (
        "You are 'Shadow', Gia's magical AI tutor and assistant.\n"
        "You live inside Gia's learning app to help her with English and Math.\n"
        "Always be encouraging, friendly, and use lots of emojis like ✨, 💖, and 🌟.\n"
        "Keep your response strictly under 3 short sentences so it can be read allowed easily.\n"
        "Speak in an engaging mix of Korean and casual English phrases.\n\n"
        f"{context_str}"
        f"Gia says: {user_message}"
    )

# @tag ASSISTANT @tag AI
@router.post("/api/assistant/chat")
async def assistant_chat(req: AssistantChatRequest) -> dict:
    """Handle chat message from the floating Shadow widget."""
    safe_message = req.message.strip()[:1000]
    if not safe_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
        
    prompt = _build_system_prompt(safe_message, req.context)

    # 1. Try Gemini (Primary for rich chatting)
    if GEMINI_API_KEY:
        try:
            gemini_url = (
                "https://generativelanguage.googleapis.com/v1/models/"
                "gemini-1.5-flash:generateContent"
            )
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    gemini_url,
                    json={"contents": [{"parts": [{"text": prompt}]}]},
                    headers={"x-goog-api-key": GEMINI_API_KEY},
                )
                if resp.status_code == 200:
                    text = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                    if text:
                        return {"message": text}
        except Exception as e:
            logger.warning(f"Gemini assistant failed: {e}")
            pass # Fall back to Ollama

    # 2. Try Ollama (Offline fallback)
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{OLLAMA_HOST}/api/generate",
                json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            )
            if resp.status_code == 200:
                text = resp.json().get("response", "").strip()
                if text:
                    return {"message": text}
    except Exception as e:
        logger.warning(f"Ollama assistant failed: {e}")
        pass

    raise HTTPException(status_code=503, detail="AI Assistant is currently unavailable.")
