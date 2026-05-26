"""
backend/services/math_diagnostic.py — Math wrong-answer diagnostic engine.

When a learner answers incorrectly:
1) Extract which choice (A/B/C/D) was selected
2) Look up error_type + misconception_id from problem.expected_errors[choice]
3) If misconception_id is missing, infer from misconception_candidates using error_type
4) Synthesize diagnosis result with short_label/description/example from the library

Design principles:
- Pure function (no DB): easy unit testing via in/out
- Library loaded once on module import, then LRU-cached
- Safe fallback on match failure (error_type='concept_gap', misconception_id=None)
"""

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).parent.parent / "data" / "math"

# === Library loader ===

@lru_cache(maxsize=8)
def _load_misconception_library(grade: str) -> dict:
    """{ccss: {ids: {mid: misc_dict}, ets: {error_type: mid}}}"""
    lib_dir = _DATA_DIR / grade / "misconceptions"
    out: dict = {}
    if not lib_dir.exists():
        return out
    for path in lib_dir.glob("*.json"):
        try:
            with open(path, encoding="utf-8") as fh:
                d = json.load(fh)
        except (json.JSONDecodeError, OSError, UnicodeDecodeError) as e:
            logger.warning("misconception lib parse fail %s: %s", path, e)
            continue
        ccss = d.get("standard") or path.stem
        ids = {}
        ets = {}
        for m in d.get("misconceptions", []) or []:
            mid = m.get("misconception_id")
            et = m.get("error_type")
            if mid:
                ids[mid] = m
                if et:
                    ets[et] = mid
        out[ccss] = {"ids": ids, "ets": ets}
    return out


def clear_library_cache() -> None:
    """Call after unit tests or a data hot-reload."""
    _load_misconception_library.cache_clear()


def _resolve_lib_entry(ccss: str, lib: dict):
    """Exact match → parent-standard fallback."""
    if not ccss:
        return None
    if ccss in lib:
        return lib[ccss]
    # Child → parent: strip a trailing lowercase letter (3.NF.A.3a → 3.NF.A.3)
    if ccss[-1].isalpha() and ccss[-1].islower():
        parent = ccss[:-1]
        if parent in lib:
            return lib[parent]
    return None


# === Choice extraction ===

def extract_user_choice(user_answer: str, choices: list, correct_raw: str = "") -> Optional[str]:
    """
    Determine which choice (A/B/C/D...) user_answer corresponds to. None on no match.

    Match priority:
      1) user_answer is exactly one letter (A-H) within the choices range → that letter
      2) user_answer has a label prefix like "B) 588" → first letter
      3) text match against a choice (comparing with the label stripped) → that label
    """
    if not user_answer or not choices:
        return None
    ua = str(user_answer).strip()
    # 1) single-letter label
    if len(ua) == 1 and ua.upper() in "ABCDEFGH":
        idx = ord(ua.upper()) - 65
        if 0 <= idx < len(choices):
            return ua.upper()
    # 2) prefix like "B) 588"
    if len(ua) >= 2 and ua[0].upper() in "ABCDEFGH" and ua[1] in ")":
        return ua[0].upper()
    # 3) text match
    ua_lower = ua.lower()
    for c in choices:
        if not isinstance(c, str) or len(c) < 2:
            continue
        label = c[0].upper() if c[0].upper() in "ABCDEFGH" else None
        clean = c.split(")", 1)[-1].strip().lower() if ")" in c else c.strip().lower()
        if ua_lower == c.strip().lower() or ua_lower == clean:
            return label
    return None


# === Main diagnostic function ===

def diagnose(problem: dict, user_answer: str, grade: str = "G3", *, is_correct: bool = False) -> dict:
    """
    Synthesize a diagnosis result for a wrong answer.

    Returned dict (passes through with an empty result when correct):
      {
        "error_type": "concept_gap",          # item/library match result (when wrong)
        "misconception_id": "3.NBT.A.2.M03" | None,
        "short_label": "..." | None,
        "note": "...",                         # short explanation shown to the learner
        "candidates": [...]                    # other possibilities (usable as UI hints)
      }
    """
    if is_correct:
        return {"error_type": "none", "misconception_id": None,
                "short_label": None, "note": "", "candidates": []}

    if not isinstance(problem, dict):
        return _generic_fallback()

    ccss = problem.get("ccss")
    if isinstance(ccss, list):
        ccss = ccss[0] if ccss else None
    expected_errors = problem.get("expected_errors") or {}
    # list-shape guard: some legacy items use a [strings] format → convert to a _wrong key
    if isinstance(expected_errors, list):
        joined = "; ".join(str(x) for x in expected_errors if x)
        expected_errors = {"_wrong": {"error_type": "concept_gap", "note": joined}} if joined else {}
    elif not isinstance(expected_errors, dict):
        expected_errors = {}
    candidates = problem.get("misconception_candidates") or []
    choices = problem.get("choices") or []

    lib = _load_misconception_library(grade)
    lib_entry = _resolve_lib_entry(ccss, lib)

    # 1) identify the choice → look up expected_errors
    choice_label = extract_user_choice(user_answer, choices, problem.get("correct_answer", ""))
    chosen_ee: dict = {}
    if choice_label and choice_label in expected_errors:
        chosen_ee = expected_errors[choice_label] or {}
    elif "_wrong" in expected_errors:
        chosen_ee = expected_errors["_wrong"] or {}
    else:
        # Not multiple-choice or no match — try the first expected_errors entry
        for k, v in expected_errors.items():
            if isinstance(v, dict):
                chosen_ee = v
                break

    error_type = chosen_ee.get("error_type") or "concept_gap"
    misconception_id = chosen_ee.get("misconception_id")
    note = chosen_ee.get("note") or ""

    # 2) infer misconception_id (if missing, map error_type → library)
    if not misconception_id and lib_entry:
        ets = lib_entry.get("ets", {})
        if error_type in ets:
            misconception_id = ets[error_type]

    # 3) synthesize library details
    short_label = None
    if misconception_id and lib_entry:
        m = lib_entry.get("ids", {}).get(misconception_id)
        if m:
            short_label = m.get("short_label")
            # if note is empty, use part of the library description
            if not note:
                note = m.get("short_label") or m.get("description", "")[:160]

    return {
        "error_type": error_type,
        "misconception_id": misconception_id,
        "short_label": short_label,
        "note": note,
        "candidates": candidates,
    }


def _generic_fallback() -> dict:
    return {
        "error_type": "concept_gap",
        "misconception_id": None,
        "short_label": None,
        "note": "Review the concept and check each solution step carefully.",
        "candidates": [],
    }


def get_misconception(grade: str, misconception_id: str) -> Optional[dict]:
    """Fetch a full library entry by ID (for dashboard/coaching UI)."""
    if not misconception_id:
        return None
    lib = _load_misconception_library(grade)
    for ccss, entry in lib.items():
        m = entry.get("ids", {}).get(misconception_id)
        if m:
            return {"ccss": ccss, **m}
    return None
