"""
routers/math_kangaroo_helpers.py — Pure helpers for Math Kangaroo router
Section: Math
Dependencies: models (XPLog), utils (validate_safe_id)

No FastAPI routes here — only loading, parsing, formatting, and XP utility
functions shared by math_kangaroo.py.
"""

import json
import logging
from datetime import date, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

try:
    from ..models import XPLog
    from ..utils import validate_safe_id as _validate_safe_id
except ImportError:  # pragma: no cover — fallback for direct execution
    from models import XPLog
    from utils import validate_safe_id as _validate_safe_id

logger = logging.getLogger(__name__)

KANGAROO_DIR = Path(__file__).parent.parent / "data" / "math" / "kangaroo"
PDF_DIR = Path(__file__).parent.parent.parent / "frontend" / "static" / "math" / "kangaroo" / "pdf"

# Map set_id prefix → short competition label shown on cards
COMPETITION_LABELS: dict[str, str] = {
    "ikmc":  "IKMC",
    "cyp":   "CYP",
    "usa":   "USA",
    "ksf":   "KSF",
    "leb":   "Lebanon",
    "intl":  "International",
    "india": "India",
}


def competition_label(set_id: str) -> str:
    prefix = set_id.split("_")[0].lower()
    return COMPETITION_LABELS.get(prefix, prefix.upper())


def is_past_paper(data: dict[str, Any]) -> bool:
    return data.get("source_type") == "official_past_paper" or bool(data.get("pdf_file"))


_SEC_KEYS = ("section_one", "section_two", "section_three")
_SEC_DEFAULT_NAMES = {
    "section_one": "Section One",
    "section_two": "Section Two",
    "section_three": "Section Three",
}


def _range_str_to_labels(range_str: str) -> list[str]:
    """Convert '1-8' or '9-16' range strings to ['1','2',...,'8']."""
    try:
        start, end = range_str.split("-")
        return [str(n) for n in range(int(start), int(end) + 1)]
    except (ValueError, AttributeError):
        return []


def past_paper_sections(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Build a unified section list using numbering (labels) + scoring (points).

    Returns [{key, name, points, questions: [label,...], prefix?}]. Supports
    two scoring formats:
    - Old: scoring.section_one/two/three with questions list
    - New: scoring.section1_questions ('1-8') + scoring.section1_points
    When a `numbering` block is present its labels (e.g. A1..C8) win.
    """
    scoring = data.get("scoring") or {}
    numbering = data.get("numbering") or {}
    num_sections = numbering.get("sections") or []
    out: list[dict[str, Any]] = []

    # New schema: section1_questions / section1_points
    if "section1_points" in scoring:
        new_defs = [
            ("section_one",   "Section One",   "section1_questions",  "section1_points"),
            ("section_two",   "Section Two",   "section2_questions",  "section2_points"),
            ("section_three", "Section Three", "section3_questions",  "section3_points"),
        ]
        for i, (key, default_name, q_key, p_key) in enumerate(new_defs):
            pts = int(scoring.get(p_key, 0) or 0)
            if not pts:
                continue
            q_val = scoring.get(q_key, "")
            if i < len(num_sections):
                num_sec = num_sections[i]
                labels = [str(q) for q in (num_sec.get("questions") or [])]
                name = num_sec.get("name") or default_name
                prefix = num_sec.get("prefix")
            else:
                labels = _range_str_to_labels(str(q_val)) if isinstance(q_val, str) else [str(q) for q in (q_val or [])]
                name = default_name
                prefix = None
            entry: dict[str, Any] = {"key": key, "name": name, "points": pts, "questions": labels}
            if prefix:
                entry["prefix"] = prefix
            out.append(entry)
        return out

    # Old schema: scoring.section_one / section_two / section_three
    for i, key in enumerate(_SEC_KEYS):
        sec = scoring.get(key)
        if not sec:
            continue
        pts = int(sec.get("points", 0) or 0)
        if i < len(num_sections):
            num_sec = num_sections[i]
            labels = [str(q) for q in (num_sec.get("questions") or [])]
            name = num_sec.get("name") or _SEC_DEFAULT_NAMES[key]
            prefix = num_sec.get("prefix")
        else:
            labels = [str(q) for q in (sec.get("questions") or [])]
            name = _SEC_DEFAULT_NAMES[key]
            prefix = None
        entry = {"key": key, "name": name, "points": pts, "questions": labels}
        if prefix:
            entry["prefix"] = prefix
        out.append(entry)
    return out


def pdf_available(pdf_file: Optional[str]) -> bool:
    """Check whether the local PDF file exists (PDFs not committed to git)."""
    if not pdf_file:
        return False
    rel = pdf_file.lstrip("/")
    if rel.startswith("static/"):
        rel = rel[len("static/"):]
    p = Path(__file__).parent.parent.parent / "frontend" / "static" / rel
    return p.is_file()


# ── Helpers ─────────────────────────────────────────────────

# @tag MATH @tag KANGAROO
@lru_cache(maxsize=128)
def read_set_cached(path_str: str, mtime: float) -> dict[str, Any]:
    """Parse a kangaroo set JSON keyed by (path, mtime)."""
    return json.loads(Path(path_str).read_text("utf-8"))


# @tag MATH @tag KANGAROO
def load_set(set_id: str) -> dict[str, Any]:
    """Load a Kangaroo set JSON by id or raise 404 (cached by mtime).

    set_id is validated against path traversal — only alphanumeric+underscore+hyphen.
    """
    set_id = _validate_safe_id(set_id, "set_id", max_len=80)
    path = KANGAROO_DIR / f"{set_id}.json"
    # Double-check resolved path is under KANGAROO_DIR
    try:
        path.resolve().relative_to(KANGAROO_DIR.resolve())
    except (ValueError, OSError):
        raise HTTPException(status_code=400, detail="Invalid set_id")
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Set {set_id} not found")
    try:
        return read_set_cached(str(path), path.stat().st_mtime)
    except json.JSONDecodeError as exc:
        logger.exception("Invalid JSON in %s", path)
        raise HTTPException(status_code=500, detail="Corrupt set data") from exc


# @tag MATH @tag KANGAROO
def clear_caches() -> None:
    """Drop cached set JSONs (call after bulk file edits)."""
    read_set_cached.cache_clear()


# @tag MATH @tag KANGAROO
def iter_questions(data: dict[str, Any]):
    """Yield (section_name, points_per_q, question) tuples for a loaded set."""
    for section in data.get("sections", []) or []:
        pts = int(section.get("points_per_question", 0) or 0)
        name = section.get("name", "")
        for q in section.get("questions", []) or []:
            yield name, pts, q


# @tag MATH @tag KANGAROO
def grade_label(percentage: float) -> str:
    """Return an encouraging label for a score percentage."""
    if percentage >= 90:
        return "Outstanding!"
    if percentage >= 80:
        return "Excellent!"
    if percentage >= 70:
        return "Great job!"
    if percentage >= 60:
        return "Good effort!"
    return "Keep practicing!"


# @tag MATH @tag KANGAROO
def format_time(seconds: Optional[int]) -> str:
    """Format seconds as mm:ss."""
    s = max(0, int(seconds or 0))
    return f"{s // 60:02d}:{s % 60:02d}"


# @tag MATH @tag KANGAROO @tag XP
def award_kangaroo_xp(db: Session, set_id: str, action: str, amount: int) -> int:
    """Insert an XPLog row directly (per-set dedup so each set awards once per tier).

    Uses the correct action key per tier so XP_RULES overrides and source attribution work.
    """
    if amount <= 0:
        return 0
    today = date.today().isoformat()
    detail = f"kangaroo:{set_id}"
    existing = db.query(XPLog).filter(
        XPLog.action == action,
        XPLog.detail == detail,
        XPLog.earned_date == today,
    ).first()
    if existing:
        return 0
    db.add(XPLog(
        action=action,
        xp_amount=amount,
        detail=detail,
        earned_date=today,
        source="math",
        created_at=datetime.now().isoformat(),
    ))
    return amount
