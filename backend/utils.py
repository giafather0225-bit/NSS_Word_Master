"""
utils.py — shared helpers (LLM/OCR parsing + path-safety validators).
"""
from __future__ import annotations

import json
import re

from fastapi import HTTPException


# ── Path-safety validators (used by routers/lessons.py et al.) ────────

_SAFE_LESSON_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_-]{0,39}$')
_SAFE_NAME_RE   = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_\- ]{0,49}$')


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


def parse_json_array(text: str) -> list[dict] | None:
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
