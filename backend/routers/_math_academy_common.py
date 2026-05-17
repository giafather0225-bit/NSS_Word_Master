"""
_math_academy_common.py — Shared helpers, constants, and schemas for Math Academy routers.
Section: Math
Dependencies: models.math, models.system, services.xp_engine, services.streak_engine, utils
API endpoints: none (shared utility, not a router)

Imported by:
  math_academy.py           — catalog + round + stage endpoints
  math_academy_lifecycle.py — complete-lesson + unit-test/submit
  math_academy_flow.py      — pre-test + learn + try + exit-quiz
  math_spaced_review.py     — spaced review count/today/submit
"""

import json
import logging
import re
from datetime import datetime
from fractions import Fraction
from functools import lru_cache
from pathlib import Path
from typing import Optional

from fastapi import HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

try:
    from ..database import get_db
    from ..models import MathProblem, MathProgress, MathAttempt, MathWrongReview, MathSpacedReview
    from ..models.math import MathUnitTest
    from ..models.system import AppConfig
    from ..services import xp_engine, streak_engine
    from ..services.math_diagnostic import diagnose as _diagnose_attempt
    from ..utils import validate_safe_id as _validate_safe_id
except ImportError:
    from database import get_db
    from models import MathProblem, MathProgress, MathAttempt, MathWrongReview, MathSpacedReview
    from models.math import MathUnitTest
    from models.system import AppConfig
    from services import xp_engine, streak_engine
    from services.math_diagnostic import diagnose as _diagnose_attempt
    from utils import validate_safe_id as _validate_safe_id

# ── Constants ─────────────────────────────────────────────────────────────────

MATH_UNIT_TEST_PASS_RATIO = 0.8

_DATA_DIR = Path(__file__).parent.parent / "data" / "math"

_SPACED_INTERVALS: dict[str, list[int]] = {
    "A": [14, 28],      # ≥90%
    "B": [7, 14, 28],   # 70-89%
    "C": [3, 7, 14],    # 50-69%
    "D": [1, 3, 7],     # <50%
}

# ── Answer helpers ────────────────────────────────────────────────────────────

# @tag MATH @tag ACADEMY
def _normalize_math_answer(s: str) -> str:
    """Normalize a raw answer string for tolerant comparison."""
    s = (s or "").strip().lower()
    s = s.lstrip("$").rstrip("%")
    s = s.replace(",", "")
    s = re.sub(r"\s+", " ", s)
    return s


# @tag MATH @tag ACADEMY
def _to_number(s: str) -> Optional[float]:
    """Parse a normalized answer as a number — supports decimals and fractions."""
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        pass
    if "/" in s:
        try:
            return float(Fraction(s.replace(" ", "")))
        except (ValueError, ZeroDivisionError):
            return None
    return None


# @tag MATH @tag ACADEMY
def _answers_equivalent(user: str, correct: str) -> bool:
    """Compare answers tolerantly: numeric equality first, else string equality."""
    u = _normalize_math_answer(user)
    c = _normalize_math_answer(correct)
    if u == c:
        return True
    un, cn = _to_number(u), _to_number(c)
    if un is not None and cn is not None:
        return abs(un - cn) < 1e-9
    return False


# ── File I/O ──────────────────────────────────────────────────────────────────

# @tag MATH @tag ACADEMY
@lru_cache(maxsize=512)
def _read_json_cached(path_str: str, mtime: float) -> dict:
    """Parse JSON keyed by (path, mtime) — file edits auto-invalidate."""
    try:
        return json.loads(Path(path_str).read_text("utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Failed to parse lesson JSON %s: %s", path_str, exc)
        return {}


# @tag MATH @tag ACADEMY
def _safe_math_path(*parts: str) -> Path:
    """Resolve a path under _DATA_DIR after validating each component is path-safe.

    Each part is validated against path traversal — only alphanumeric + `_-` allowed,
    optionally with a single `.json` suffix on the last segment. After joining,
    the resolved path must still live under _DATA_DIR (symlink-escape guard).
    Raises HTTPException(400) on any violation.
    """
    for p in parts:
        base = p[:-5] if p.endswith(".json") else p
        _validate_safe_id(base, "math path component", max_len=80)
    candidate = _DATA_DIR.joinpath(*parts)
    try:
        resolved = candidate.resolve()
        resolved.relative_to(_DATA_DIR.resolve())
    except (ValueError, OSError):
        raise HTTPException(status_code=400, detail="Invalid math path")
    return candidate


# @tag MATH @tag ACADEMY
def _load_lesson_json(grade: str, unit: str, lesson: str) -> dict:
    """Load a lesson JSON file from data/math/{grade}/{unit}/{lesson}.json (cached)."""
    path = _safe_math_path(grade, unit, f"{lesson}.json")
    if not path.exists():
        return {}
    return _read_json_cached(str(path), path.stat().st_mtime)


# @tag MATH @tag ACADEMY
def clear_caches() -> None:
    """Drop cached lesson JSON."""
    _read_json_cached.cache_clear()


# ── Data helpers ──────────────────────────────────────────────────────────────

# @tag MATH @tag ACADEMY
def _get_or_create_progress(
    db: Session,
    grade: str,
    unit: str,
    lesson: str,
    **defaults,
) -> "MathProgress":
    """Fetch or atomically create MathProgress(grade, unit, lesson).

    Handles the TOCTOU race: if two concurrent requests both see no row and
    both try to INSERT, the second hits the UNIQUE(grade, unit, lesson)
    constraint. We catch IntegrityError, rollback, and re-fetch.
    """
    from sqlalchemy.exc import IntegrityError

    prog = db.query(MathProgress).filter_by(grade=grade, unit=unit, lesson=lesson).first()
    if prog:
        return prog
    try:
        prog = MathProgress(grade=grade, unit=unit, lesson=lesson, **defaults)
        db.add(prog)
        db.flush()
    except IntegrityError:
        db.rollback()
        prog = db.query(MathProgress).filter_by(grade=grade, unit=unit, lesson=lesson).first()
    return prog


# @tag MATH @tag ACADEMY
def _normalize_item(item: dict) -> dict:
    """Normalize item field aliases (U8 uses `question` + lowercase `type`)."""
    if not isinstance(item, dict):
        return item
    out = dict(item)
    if "stem" not in out and "question" in out:
        out["stem"] = out["question"]
    if "answer" not in out and "correct_answer" in out:
        out["answer"] = out["correct_answer"]
    if "correct_answer" not in out and "answer" in out:
        out["correct_answer"] = out["answer"]
    t = out.get("type")
    if isinstance(t, str):
        out["type"] = t.upper() if t.lower() in {"mc", "card"} else t
    return out


# @tag MATH @tag ACADEMY
def _stage_problems(data: dict, stage: str, exit_quiz_attempt: int = 1) -> list:
    """Extract stage problems from any lesson schema.

    U1 schema: top-level key per stage (data["pretest"], data["learn"], ...).
    U2 schema: single data["items"] list where each item has a "section" field.
    U8 schema: data["sections"][stage] wrapper with renamed item fields.

    exit_quiz fallback: if no exit_quiz key, use practice_r1/r2/r3 by attempt number.
    """
    if stage in data and isinstance(data[stage], list):
        return [_normalize_item(it) for it in data[stage]]
    sections = data.get("sections")
    if isinstance(sections, dict) and isinstance(sections.get(stage), list):
        return [_normalize_item(it) for it in sections[stage]]
    items = data.get("items")
    if isinstance(items, list):
        result = [_normalize_item(it) for it in items if it.get("section") == stage]
        if result:
            return result
    if stage == "exit_quiz":
        pool_key = {1: "practice_r1", 2: "practice_r2", 3: "practice_r3"}.get(exit_quiz_attempt, "practice_r1")
        fallback = _stage_problems(data, pool_key)
        return fallback[:5] if fallback else []
    return []


# @tag MATH @tag ACADEMY
def _natural_key(name: str) -> list:
    """Natural sort key — splits digit runs so "U2" sorts before "U10"."""
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", name)]


# @tag MATH @tag ACADEMY
def _list_dirs(parent: Path) -> list[str]:
    """List subdirectory names under parent in natural order."""
    if not parent.is_dir():
        return []
    names = [
        d.name for d in parent.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    ]
    return sorted(names, key=_natural_key)


# @tag MATH @tag ACADEMY
def _list_json_files(parent: Path) -> list[str]:
    """List JSON filenames (without .json) in natural order."""
    if not parent.is_dir():
        return []
    names = [
        f.stem for f in parent.iterdir()
        if f.suffix == ".json" and not f.name.startswith(".")
    ]
    return sorted(names, key=_natural_key)


# ── v2.0 helpers ──────────────────────────────────────────────────────────────

def _spaced_schedule(score_pct: float) -> list[int]:
    """Return interval list for a given exit-quiz score percentage."""
    if score_pct >= 90:
        return _SPACED_INTERVALS["A"]
    if score_pct >= 70:
        return _SPACED_INTERVALS["B"]
    if score_pct >= 50:
        return _SPACED_INTERVALS["C"]
    return _SPACED_INTERVALS["D"]


def _grade_answer(problem: dict, user_answer: str) -> tuple[bool, str]:
    """Grade a single answer against a problem dict. Returns (is_correct, correct_display)."""
    correct_raw = str(problem.get("correct_answer", problem.get("answer", ""))).strip()
    user_raw = user_answer.strip()
    choices = problem.get("choices", [])
    correct_display = correct_raw

    if correct_raw.upper() in "ABCDEFGH" and len(correct_raw) == 1 and choices:
        correct_idx = ord(correct_raw.upper()) - 65
        if 0 <= correct_idx < len(choices):
            correct_text = choices[correct_idx]
            clean_correct = correct_text.split(")", 1)[-1].strip() if ")" in correct_text else correct_text.strip()
            correct_display = clean_correct or correct_text.strip()
            is_correct = (
                user_raw.lower() == correct_raw.lower()
                or user_raw.lower() == clean_correct.lower()
                or user_raw.lower() == correct_text.strip().lower()
            )
        else:
            is_correct = user_raw.lower() == correct_raw.lower()
    elif correct_raw.lower() in ("true", "false"):
        is_correct = user_raw.lower() == correct_raw.lower()
    else:
        is_correct = _answers_equivalent(user_raw, correct_raw)

    return is_correct, correct_display


def _decide_next_after_round(prog: "MathProgress", current_round: str,
                             score: int, total: int) -> tuple[str, bool]:
    """Mastery Gating 결정.

    규칙
    - R1 perfect (100%) AND PT mastery (PT 100%) → R2 skip → R3 직행
    - 그 외 정상 진행: R1 → R2 → R3 → complete
    - R3 완료 시 → complete

    반환 (next_stage, mastery_skip_applied)
    """
    r_pct = (score / total * 100) if total else 0
    if current_round == "practice_r1":
        if r_pct >= 100.0 and (prog.pretest_mastery or False):
            return "practice_r3", True
        return "practice_r2", False
    if current_round == "practice_r2":
        return "practice_r3", False
    if current_round == "practice_r3":
        return "complete", False
    return current_round, False


# ── Spaced review helpers ─────────────────────────────────────────────────────

def _unit_number(unit_id: str) -> int:
    """Extract numeric unit index from a unit id string (e.g. 'U4_...' → 4)."""
    m = re.search(r"[Uu](\d+)", unit_id or "")
    return int(m.group(1)) if m else 0


def _lesson_name(lesson_id: str) -> str:
    """Extract just the lesson file name from a lesson_id ('grade/unit/lesson' → 'lesson')."""
    return lesson_id.rsplit("/", 1)[-1]


def _answer_display(problem: dict) -> str:
    """Return human-readable correct answer (resolves letter keys to choice text)."""
    correct_raw = str(problem.get("correct_answer", problem.get("answer", ""))).strip()
    choices = problem.get("choices", [])
    if correct_raw.upper() in "ABCDEFGH" and len(correct_raw) == 1 and choices:
        idx = ord(correct_raw.upper()) - 65
        if 0 <= idx < len(choices):
            text = choices[idx]
            return text.split(")", 1)[-1].strip() if ")" in text else text.strip()
    return correct_raw


def _weakness_score(sr: "MathSpacedReview", wrong_counts: dict[str, int]) -> int:
    """Weakness score = (100 - exit_quiz_pct) + wrong_review_count × 10."""
    eq_pct = int(round((sr.exit_quiz_score / 5) * 100)) if sr.exit_quiz_score else 50
    wc = wrong_counts.get(sr.lesson_id, 0)
    return max(0, 100 - eq_pct) + wc * 10


def _build_sr_problem(p: dict, lesson_id: str, unit_id: str, grade: str, title: str) -> dict:
    """Serialize a problem dict for spaced review response."""
    p = _normalize_item(p)
    fb = p.get("feedback", {})
    explanation = fb.get("incorrect", fb.get("correct", ""))
    return {
        "lesson_id": lesson_id,
        "unit_id": unit_id,
        "grade": grade,
        "lesson_title": title,
        "problem_id": p.get("id", ""),
        "stem": p.get("stem", p.get("question", "")),
        "type": p.get("type", "short"),
        "choices": p.get("choices", []),
        "correct_answer": str(p.get("correct_answer", p.get("answer", ""))).strip(),
        "answer_display": _answer_display(p),
        "explanation": explanation,
    }


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class SubmitAnswerIn(BaseModel):
    problem_id: str = Field(..., max_length=80)
    grade: str = Field(..., max_length=10)
    unit: str = Field(..., max_length=80)
    lesson: str = Field(..., max_length=80)
    stage: str = Field(..., max_length=20)
    user_answer: str = Field("", max_length=200)
    time_spent_sec: int = 0

    def clean(self):
        self.user_answer = self.user_answer.strip()[:200]
        return self


class CompleteLessonIn(BaseModel):
    grade: str = Field(..., max_length=10)
    unit: str = Field(..., max_length=80)
    lesson: str = Field(..., max_length=80)


class SubmitUnitTestIn(BaseModel):
    grade: str = Field(..., max_length=10)
    unit: str = Field(..., max_length=80)
    score: int = Field(..., ge=0)
    total: int = Field(..., ge=1)


class PreTestSubmitIn(BaseModel):
    grade: str = Field(..., max_length=10)
    unit: str = Field(..., max_length=80)
    lesson: str = Field(..., max_length=80)
    score: int = Field(..., ge=0)
    total: int = Field(5, ge=1)
    skipped: bool = False


class LearnCompleteIn(BaseModel):
    grade: str = Field(..., max_length=10)
    unit: str = Field(..., max_length=80)
    lesson: str = Field(..., max_length=80)


class TrySubmitIn(BaseModel):
    grade: str = Field(..., max_length=10)
    unit: str = Field(..., max_length=80)
    lesson: str = Field(..., max_length=80)
    problem_id: str = Field(..., max_length=80)
    user_answer: str = Field("", max_length=200)
    time_spent_sec: int = 0
    attempt_number: int = 1


class ExitQuizAnswerIn(BaseModel):
    problem_id: str = Field(..., max_length=80)
    user_answer: str = Field("", max_length=200)
    time_spent_sec: int = 0


class ExitQuizSubmitIn(BaseModel):
    grade: str = Field(..., max_length=10)
    unit: str = Field(..., max_length=80)
    lesson: str = Field(..., max_length=80)
    answers: list[ExitQuizAnswerIn] = Field(..., max_length=20)


class RoundCompleteIn(BaseModel):
    grade: str = Field(..., max_length=10)
    unit: str = Field(..., max_length=80)
    lesson: str = Field(..., max_length=80)
    round: str = Field(..., max_length=20)
    score: int = Field(..., ge=0)
    total: int = Field(..., ge=1)


class SpacedReviewAnswerIn(BaseModel):
    lesson_id: str = Field(..., max_length=80)
    unit_id: str = Field(..., max_length=80)
    grade: str = Field(..., max_length=10)
    problem_id: str = Field(..., max_length=80)
    user_answer: str = Field("", max_length=200)


class SpacedReviewSubmitIn(BaseModel):
    answers: list[SpacedReviewAnswerIn] = Field(..., max_length=50)
