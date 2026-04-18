"""
utils.py — shared helpers for parsing LLM / OCR output.
"""
from __future__ import annotations

import json
import re


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
