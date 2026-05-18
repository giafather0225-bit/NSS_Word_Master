"""
utils.py — shared helpers (LLM/OCR parsing + path-safety validators + rate limiter).
"""
from typing import Optional
from collections import deque

import json
import re
import time

from fastapi import HTTPException, Request


# ── Lightweight per-IP sliding-window rate limiter ─────────────────────

class _RateLimiter:
    """Thread-safe in-memory rate limiter (no external deps).

    Tracks request timestamps per IP in a deque.  Each Dependency call
    prunes old entries and raises 429 when the limit is exceeded.
    """
    def __init__(self, max_calls: int, window_sec: int) -> None:
        self._max   = max_calls
        self._win   = window_sec
        self._store: dict[str, deque] = {}

    def __call__(self, request: Request) -> None:
        ip  = request.client.host if request.client else "unknown"
        now = time.monotonic()
        dq  = self._store.setdefault(ip, deque())
        while dq and now - dq[0] > self._win:
            dq.popleft()
        if len(dq) >= self._max:
            raise HTTPException(
                status_code=429,
                detail=f"Too many requests — please slow down (limit {self._max}/{self._win}s).",
            )
        dq.append(now)


# Shared limiters — import and use as FastAPI Depends() in routers
tts_limiter = _RateLimiter(max_calls=40, window_sec=60)   # 40 TTS req/min
ai_limiter  = _RateLimiter(max_calls=15, window_sec=60)   # 15 AI req/min
ocr_limiter = _RateLimiter(max_calls=10, window_sec=60)   # 10 OCR req/min


# ── Path-safety validators (used by routers/lessons.py et al.) ────────

_SAFE_LESSON_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_-]{0,39}$')
_SAFE_NAME_RE   = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_\- ]{0,49}$')
_SAFE_ID_RE     = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$')


def validate_safe_id(value: str, field: str, max_len: int = 80) -> str:
    """Validate a generic path-safe identifier (grade/unit/set_id/etc).

    Blocks '..', '/', '\\', spaces, and other dangerous chars.
    Allowed: leading alphanumeric, then alphanumeric + underscore + hyphen.
    """
    v = (value or "").strip()
    if not v:
        raise HTTPException(status_code=400, detail=f"{field} required")
    if len(v) > max_len or not _SAFE_ID_RE.match(v):
        raise HTTPException(status_code=400, detail=f"Invalid {field}")
    return v


def validate_name(name: str, field: str) -> str:
    """Validate subject/textbook names — blocks path traversal and dangerous chars."""
    n = (name or "").strip()
    if not n:
        raise HTTPException(status_code=400, detail=f"{field} required")
    if not _SAFE_NAME_RE.match(n):
        raise HTTPException(status_code=400, detail=f"Invalid {field} name")
    return n


def validate_lesson(lesson: str) -> str:
    """Validate lesson name — blocks path traversal, normalizes numeric input."""
    key = (lesson or "").strip()
    if not key:
        raise HTTPException(status_code=400, detail="lesson name required")
    if key.isdigit():
        key = f"Lesson_{int(key):02d}"
    if not _SAFE_LESSON_RE.match(key):
        raise HTTPException(status_code=400, detail="Invalid lesson name")
    return key


def strip_json_fences(text: str) -> str:
    """Remove markdown code fences (```json ... ```) and return trimmed body."""
    t = re.sub(r'^```[a-zA-Z]*\s*', '', text.strip())
    if t.endswith("```"):
        t = t[:-3]
    return t.strip()


def parse_json_array(text: str) -> Optional[list[dict]]:
    """Parse a JSON array out of possibly-noisy text — robust to leading/trailing junk."""
    clean = strip_json_fences(text)
    try:
        data = json.loads(clean)
        if isinstance(data, list):
            return data
    except json.JSONDecodeError:
        pass
    lb, rb = clean.find("["), clean.rfind("]")
    if lb != -1 and rb > lb:
        try:
            data = json.loads(clean[lb : rb + 1])
            if isinstance(data, list):
                return data
        except json.JSONDecodeError:
            pass
    return None
