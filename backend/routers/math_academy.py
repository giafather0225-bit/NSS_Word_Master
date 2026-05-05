"""
routers/math_academy.py — Math Academy API (grades, units, lessons, stages)
Section: Math
Dependencies: models.py (MathProblem, MathProgress, MathAttempt), services/xp_engine.py
API: GET /api/math/academy/grades, GET /api/math/academy/{grade}/units,
     GET /api/math/academy/{grade}/{unit}/lessons,
     GET /api/math/academy/{grade}/{unit}/{lesson}/{stage},
     POST /api/math/academy/submit-answer
"""

import json
import logging
import random
import re
from datetime import date, datetime, timedelta
from fractions import Fraction
from functools import lru_cache
from pathlib import Path
from typing import Optional

# @tag MATH @tag ACADEMY
MATH_UNIT_TEST_PASS_RATIO = 0.8  # v2.0: 80% threshold

# @tag MATH @tag ACADEMY
def _normalize_math_answer(s: str) -> str:
    """Normalize a raw answer string for tolerant comparison.

    Strips whitespace, lowercases, removes leading currency symbols, trailing
    percent signs, and digit-grouping commas. Collapses internal whitespace.
    """
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

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

try:
    from ..database import get_db
    from ..models import MathProblem, MathProgress, MathAttempt, MathWrongReview, MathSpacedReview
    from ..models.math import MathUnitTest
    from ..services import xp_engine, streak_engine
except ImportError:
    from database import get_db
    from models import MathProblem, MathProgress, MathAttempt, MathWrongReview, MathSpacedReview
    from models.math import MathUnitTest
    from services import xp_engine, streak_engine

router = APIRouter()
logger = logging.getLogger(__name__)

# ── Data directory for Math problem JSON files ──
_DATA_DIR = Path(__file__).parent.parent / "data" / "math"

# ── Pydantic schemas ─────────────────────────────────────────

class SubmitAnswerIn(BaseModel):
    """Submit a single answer for a math problem."""
    problem_id: str
    grade: str
    unit: str
    lesson: str
    stage: str
    user_answer: str
    time_spent_sec: int = 0

    def clean(self):
        self.user_answer = self.user_answer.strip()[:200]
        return self

# ── Helpers ──────────────────────────────────────────────────

# @tag MATH @tag ACADEMY
@lru_cache(maxsize=512)
def _read_json_cached(path_str: str, mtime: float) -> dict:
    """Parse JSON keyed by (path, mtime) — file edits auto-invalidate."""
    return json.loads(Path(path_str).read_text("utf-8"))

# @tag MATH @tag ACADEMY
def _load_lesson_json(grade: str, unit: str, lesson: str) -> dict:
    """Load a lesson JSON file from data/math/{grade}/{unit}/{lesson}.json (cached)."""
    path = _DATA_DIR / grade / unit / f"{lesson}.json"
    if not path.exists():
        return {}
    return _read_json_cached(str(path), path.stat().st_mtime)

# @tag MATH @tag ACADEMY
def clear_caches() -> None:
    """Drop cached lesson JSON (call from admin/reload endpoints if added)."""
    _read_json_cached.cache_clear()

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
    # exit_quiz fallback: use practice rounds when no exit_quiz key exists
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
    """List subdirectory names under parent in natural order (U1, U2, ..., U10)."""
    if not parent.is_dir():
        return []
    names = [
        d.name for d in parent.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    ]
    return sorted(names, key=_natural_key)

# @tag MATH @tag ACADEMY
def _list_json_files(parent: Path) -> list[str]:
    """List JSON filenames (without .json) in natural order (L1, L2, ..., L10)."""
    if not parent.is_dir():
        return []
    names = [
        f.stem for f in parent.iterdir()
        if f.suffix == ".json" and not f.name.startswith(".")
    ]
    return sorted(names, key=_natural_key)

# ── Endpoints ────────────────────────────────────────────────

# @tag MATH @tag ACADEMY
@router.get("/api/math/academy/grades")
def get_grades() -> dict:
    """Return available grade folders (e.g., G3, G4, G5, G6)."""
    grades = [g for g in _list_dirs(_DATA_DIR) if g.startswith("G")]
    return {"grades": grades}

# @tag MATH @tag ACADEMY
@router.get("/api/math/academy/{grade}/units")
def get_units(grade: str) -> dict:
    """Return available units for a grade."""
    units = _list_dirs(_DATA_DIR / grade)
    return {"grade": grade, "units": units}

# @tag MATH @tag ACADEMY
@router.get("/api/math/academy/{grade}/{unit}/lessons")
def get_lessons(grade: str, unit: str, db: Session = Depends(get_db)) -> dict:
    """Return available lessons for a unit, with progress info."""
    lesson_names = _list_json_files(_DATA_DIR / grade / unit)
    # Filter out unit_test from lesson list
    lessons = [l for l in lesson_names if l != "unit_test"]

    # Batch progress lookup — avoid N+1 queries (one per lesson).
    prog_rows = (
        db.query(MathProgress)
        .filter(
            MathProgress.grade == grade,
            MathProgress.unit == unit,
            MathProgress.lesson.in_(lessons),
        )
        .all()
    ) if lessons else []
    prog_by_lesson = {p.lesson: p for p in prog_rows}

    result = []
    for l in lessons:
        prog = prog_by_lesson.get(l)
        result.append({
            "name": l,
            "is_completed": prog.is_completed if prog else False,
            "stage": prog.stage if prog else "pretest",
            "pretest_skipped": prog.pretest_skipped if prog else False,
        })

    # Check if unit test is available
    all_done = all(r["is_completed"] for r in result) if result else False
    has_unit_test = (_DATA_DIR / grade / unit / "unit_test.json").exists()

    return {
        "grade": grade,
        "unit": unit,
        "lessons": result,
        "unit_test_unlocked": all_done and has_unit_test,
    }

# @tag MATH @tag ACADEMY
@router.get("/api/math/academy/{grade}/{unit}/{lesson}/{stage}")
def get_stage_problems(grade: str, unit: str, lesson: str, stage: str, db: Session = Depends(get_db)) -> dict:
    """Return problems for a specific lesson stage.

    Stages: pretest, learn, try, exit_quiz, practice_r1, practice_r2, practice_r3
    """
    valid_stages = {"pretest", "pre_test", "learn", "try", "exit_quiz", "practice_r1", "practice_r2", "practice_r3"}
    if stage not in valid_stages:
        raise HTTPException(status_code=400, detail=f"Invalid stage: {stage}")

    data = _load_lesson_json(grade, unit, lesson)
    if not data:
        raise HTTPException(status_code=404, detail="Lesson data not found")

    attempt = 1
    if stage == "exit_quiz":
        prog = db.query(MathProgress).filter_by(grade=grade, unit=unit, lesson=lesson).first()
        attempt = (prog.exit_quiz_attempts or 0) + 1 if prog else 1

    problems = _stage_problems(data, stage, exit_quiz_attempt=attempt)
    return {
        "grade": grade,
        "unit": unit,
        "lesson": lesson,
        "stage": stage,
        "problems": problems,
        "count": len(problems),
    }

# @tag MATH @tag ACADEMY
@router.get("/api/math/academy/{grade}/{unit}/unit-test")
def get_unit_test(grade: str, unit: str) -> dict:
    """Return unit test problems."""
    path = _DATA_DIR / grade / unit / "unit_test.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Unit test not found")
    data = _read_json_cached(str(path), path.stat().st_mtime)
    problems = data.get("problems", data if isinstance(data, list) else [])
    return {
        "grade": grade,
        "unit": unit,
        "problems": problems,
        "count": len(problems),
        "pass_threshold": data.get("pass_threshold", 0.8),
        "time_limit_min": data.get("time_limit_min", 30),
    }

# @tag MATH @tag ACADEMY
@router.post("/api/math/academy/submit-answer")
def submit_answer(req: SubmitAnswerIn, db: Session = Depends(get_db)):
    """Submit an answer for a math problem, record attempt, update progress."""
    req.clean()
    now = datetime.now().isoformat()

    # Load problem to check answer
    data = _load_lesson_json(req.grade, req.unit, req.lesson)
    stage_problems = _stage_problems(data, req.stage)
    problem = next((p for p in stage_problems if p.get("id") == req.problem_id), None)

    if not problem:
        raise HTTPException(status_code=404, detail=f"Problem {req.problem_id} not found")

    correct_raw = str(problem.get("correct_answer", problem.get("answer", ""))).strip()
    user_raw = req.user_answer.strip()
    choices = problem.get("choices", [])

    # Resolve a single-letter answer (e.g. "C") to the actual choice text
    # (e.g. "25") so the client shows the value, not the index letter.
    correct_display = correct_raw

    is_correct = False

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

    # Record attempt
    attempt = MathAttempt(
        problem_id=req.problem_id,
        grade=req.grade,
        unit=req.unit,
        lesson=req.lesson,
        stage=req.stage,
        is_correct=is_correct,
        user_answer=req.user_answer,
        error_type="none" if is_correct else "concept_gap",
        time_spent_sec=req.time_spent_sec,
        attempted_at=now,
    )
    db.add(attempt)

    # Update or create progress
    prog = (
        db.query(MathProgress)
        .filter_by(grade=req.grade, unit=req.unit, lesson=req.lesson)
        .first()
    )
    if not prog:
        prog = MathProgress(
            grade=req.grade, unit=req.unit, lesson=req.lesson,
            stage=req.stage, last_accessed=now,
        )
        db.add(prog)

    prog.last_accessed = now
    prog.attempts = (prog.attempts or 0) + 1
    prog.stage = req.stage
    if req.stage == "practice_r3" and is_correct:
        # 마지막 라운드 정답이면 완료 가능성 체크 (advanceMathStage에서 처리)
        pass

    # NOTE: per-problem XP intentionally not awarded — XP is granted at lesson_complete
    # (math_lesson_complete: +10) and unit_test_pass (+25) per CLAUDE.md spec.
    if not is_correct:
        # Register wrong answer for spaced-repetition review (skip pretest — diagnostic only)
        if req.stage != "pretest":
            existing = (
                db.query(MathWrongReview)
                .filter_by(problem_id=req.problem_id, is_mastered=False)
                .first()
            )
            if not existing:
                next_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
                wrong = MathWrongReview(
                    problem_id=req.problem_id,
                    original_attempt_id=None,  # set after flush below
                    next_review_date=next_date,
                    interval_days=1,
                    times_reviewed=0,
                    is_mastered=False,
                )
                db.add(wrong)
                db.flush()
                wrong.original_attempt_id = attempt.id

    db.commit()

    fb = problem.get("feedback", {})
    if isinstance(fb, dict):
        feedback_text = fb.get("correct", "") if is_correct else fb.get("incorrect", fb.get("wrong", ""))
    elif isinstance(fb, str):
        feedback_text = fb
    else:
        feedback_text = ""

    if not feedback_text:
        feedback_text = problem.get("feedback_correct" if is_correct else "feedback_wrong", "")

    if not feedback_text:
        feedback_text = "Great job!" if is_correct else f"The correct answer is {correct_display}."

    return {
        "is_correct": is_correct,
        "correct_answer": correct_display,
        "feedback": feedback_text,
        "solution_steps": problem.get("solution_steps", []),
    }

# @tag MATH @tag ACADEMY
@router.get("/api/math/academy/progress/{grade}")
def get_grade_progress(grade: str, db: Session = Depends(get_db)):
    """Return progress overview for all units/lessons in a grade."""
    progs = db.query(MathProgress).filter_by(grade=grade).all()
    result = {}
    for p in progs:
        key = f"{p.unit}/{p.lesson}"
        result[key] = {
            "stage": p.stage,
            "is_completed": p.is_completed,
            "pretest_skipped": p.pretest_skipped,
            "best_score_r1": p.best_score_r1,
            "best_score_r2": p.best_score_r2,
            "best_score_r3": p.best_score_r3,
            "unit_test_passed": p.unit_test_passed,
        }
    return {"grade": grade, "progress": result}

class CompleteLessonIn(BaseModel):
    """Mark a lesson as completed."""
    grade: str
    unit: str
    lesson: str

@router.post("/api/math/academy/complete-lesson")
async def complete_lesson(req: CompleteLessonIn, db: Session = Depends(get_db)):
    prog = (
        db.query(MathProgress)
        .filter_by(grade=req.grade, unit=req.unit, lesson=req.lesson)
        .first()
    )
    if not prog:
        prog = MathProgress(
            grade=req.grade, unit=req.unit, lesson=req.lesson,
            stage="complete", is_completed=True
        )
        db.add(prog)
    else:
        prog.is_completed = True
        prog.stage = "complete"
    try:
        xp_engine.award_xp(db, "math_lesson_complete", detail=f"{req.grade}/{req.unit}/{req.lesson}")
    except Exception as e:
        logger.warning("XP award failed: %s", e)
    try:
        streak_engine.mark_math_done(db)
    except Exception as e:
        logger.warning("Streak math mark failed: %s", e)
    db.commit()
    island = {"xp_multiplier": 1.0}
    try:
        from backend.services import island_care_engine as _care
        island = _care.apply_subject_gain(db, "math", "math_lesson")
    except Exception:
        pass
    return {"status": "ok", "is_completed": True, "island": island}

class SubmitUnitTestIn(BaseModel):
    """Unit test result via JSON body."""
    grade: str
    unit: str
    score: int
    total: int

@router.post("/api/math/academy/unit-test/submit")
async def submit_unit_test_body(req: SubmitUnitTestIn, db: Session = Depends(get_db)):
    pct = (req.score / req.total * 100) if req.total else 0
    # Read pass_threshold from data file (default 0.8 = 80%)
    unit_path = _DATA_DIR / req.grade / req.unit / "unit_test.json"
    threshold = 0.8
    if unit_path.exists():
        try:
            unit_data = _read_json_cached(str(unit_path), unit_path.stat().st_mtime)
            threshold = float(unit_data.get("pass_threshold", 0.8))
        except Exception:
            pass
    passed = (pct / 100) >= threshold
    rows = (
        db.query(MathProgress)
        .filter_by(grade=req.grade, unit=req.unit)
        .all()
    )
    for row in rows:
        row.unit_test_score = req.score
        if passed:
            row.unit_test_passed = True
    _xp_awarded = 0
    if passed:
        try:
            _xp_awarded = xp_engine.award_xp(db, "math_unit_test_pass", detail=f"{req.grade}/{req.unit}")
        except Exception as e:
            logger.warning("XP award failed: %s", e)
        try:
            streak_engine.mark_math_done(db)
        except Exception as e:
            logger.warning("Streak math mark failed: %s", e)
    # Record MathUnitTest row for parent dashboard history
    try:
        _attempt_num = db.query(MathUnitTest).filter_by(grade=req.grade, unit_id=req.unit).count() + 1
        db.add(MathUnitTest(
            unit_id=req.unit, grade=req.grade,
            attempt_number=_attempt_num,
            score=req.score, total=req.total,
            passed=passed,
            xp_awarded=_xp_awarded,
            taken_at=datetime.now().isoformat(),
        ))
    except Exception as e:
        logger.warning("MathUnitTest record failed: %s", e)
    db.commit()
    result = {
        "status": "ok", "passed": passed,
        "score": req.score, "total": req.total,
        "pct": round(pct, 1),
        "xp_earned": _xp_awarded,
        "island": {"xp_multiplier": 1.0},
    }
    if passed:
        try:
            from backend.services import island_care_engine as _care
            result["island"] = _care.apply_subject_gain(db, "math", "math_unit_test")
        except Exception:
            pass
    if not passed:
        try:
            weak = (
                db.query(MathAttempt.lesson, func.count(MathAttempt.id).label("cnt"))
                .filter_by(grade=req.grade, unit=req.unit, is_correct=False)
                .group_by(MathAttempt.lesson)
                .order_by(func.count(MathAttempt.id).desc())
                .first()
            )
            if weak:
                result["weak_lesson"] = weak.lesson
        except Exception as exc:
            logger.debug("Weak-lesson lookup failed for grade=%s unit=%s: %s", req.grade, req.unit, exc)
    return result


# ════════════════════════════════════════════════════════════
#  MATH_SPEC v2.0 — pre_test → learn → try → exit_quiz flow
# ════════════════════════════════════════════════════════════

# @tag MATH @tag ACADEMY
_SPACED_INTERVALS: dict[str, list[int]] = {
    "A": [14, 28],      # ≥90%
    "B": [7, 14, 28],   # 70-89%
    "C": [3, 7, 14],    # 50-69%
    "D": [1, 3, 7],     # <50%
}


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


# ── v2.0 Pydantic schemas ─────────────────────────────────────

class PreTestSubmitIn(BaseModel):
    grade: str
    unit: str
    lesson: str
    score: int
    total: int = 5
    skipped: bool = False


class LearnCompleteIn(BaseModel):
    grade: str
    unit: str
    lesson: str


class TrySubmitIn(BaseModel):
    grade: str
    unit: str
    lesson: str
    problem_id: str
    user_answer: str
    time_spent_sec: int = 0
    attempt_number: int = 1  # 1 = first attempt, 2 = retry (2-stage feedback)


class ExitQuizAnswerIn(BaseModel):
    problem_id: str
    user_answer: str
    time_spent_sec: int = 0


class ExitQuizSubmitIn(BaseModel):
    grade: str
    unit: str
    lesson: str
    answers: list[ExitQuizAnswerIn]


# ── v2.0 Endpoints ────────────────────────────────────────────

# @tag MATH @tag ACADEMY
@router.get("/api/math/academy/lesson/{grade}/{unit}/{lesson}/stage")
def get_lesson_stage(grade: str, unit: str, lesson: str, db: Session = Depends(get_db)):
    """Return current stage for lesson resume (v2.0)."""
    prog = db.query(MathProgress).filter_by(grade=grade, unit=unit, lesson=lesson).first()
    if not prog:
        return {
            "grade": grade, "unit": unit, "lesson": lesson,
            "stage": "pre_test", "is_completed": False,
            "exit_quiz_attempts": 0, "exit_quiz_score": None, "pretest_skipped": False,
        }
    # Normalize legacy stage name
    stage = "pre_test" if prog.stage == "pretest" else (prog.stage or "pre_test")
    return {
        "grade": grade, "unit": unit, "lesson": lesson,
        "stage": stage,
        "is_completed": prog.is_completed,
        "exit_quiz_attempts": prog.exit_quiz_attempts or 0,
        "exit_quiz_score": prog.exit_quiz_score,
        "pretest_skipped": prog.pretest_skipped,
    }


# @tag MATH @tag ACADEMY
@router.post("/api/math/academy/pre-test/submit")
def submit_pre_test(req: PreTestSubmitIn, db: Session = Depends(get_db)):
    """Record pre-test diagnostic result and advance stage to 'learn' (v2.0).

    Pre-test is diagnostic only — stage always advances to 'learn' regardless of score.
    """
    now = datetime.now().isoformat()
    prog = db.query(MathProgress).filter_by(grade=req.grade, unit=req.unit, lesson=req.lesson).first()
    if not prog:
        prog = MathProgress(grade=req.grade, unit=req.unit, lesson=req.lesson, last_accessed=now)
        db.add(prog)

    pct = (req.score / req.total * 100) if req.total else 0
    prog.pretest_score = req.score
    prog.pretest_passed = pct >= 80
    prog.pretest_skipped = req.skipped
    prog.stage = "learn"
    prog.last_accessed = now
    db.commit()

    return {
        "status": "ok",
        "next_stage": "learn",
        "score": req.score,
        "total": req.total,
        "pct": round(pct, 1),
        "passed": prog.pretest_passed,
    }


# @tag MATH @tag ACADEMY
@router.post("/api/math/academy/learn/complete")
def complete_learn_stage(req: LearnCompleteIn, db: Session = Depends(get_db)):
    """Mark learn stage complete and advance to 'try' (v2.0)."""
    now = datetime.now().isoformat()
    prog = db.query(MathProgress).filter_by(grade=req.grade, unit=req.unit, lesson=req.lesson).first()
    if not prog:
        prog = MathProgress(grade=req.grade, unit=req.unit, lesson=req.lesson, stage="try", last_accessed=now)
        db.add(prog)
    else:
        prog.stage = "try"
        prog.last_accessed = now
    db.commit()
    return {"status": "ok", "next_stage": "try"}


# @tag MATH @tag ACADEMY
@router.post("/api/math/academy/try/submit")
def submit_try(req: TrySubmitIn, db: Session = Depends(get_db)):
    """Submit a single try-stage answer with 2-stage feedback (v2.0).

    attempt_number=1 → first_wrong feedback (descriptive + retry hint).
    attempt_number=2 → second_wrong feedback (misconception + CPA fallback + reveal).
    """
    now = datetime.now().isoformat()

    data = _load_lesson_json(req.grade, req.unit, req.lesson)
    problems = _stage_problems(data, "try")
    problem = next((p for p in problems if p.get("id") == req.problem_id), None)
    if not problem:
        raise HTTPException(status_code=404, detail=f"Problem {req.problem_id} not found in try stage")

    is_correct, correct_display = _grade_answer(problem, req.user_answer)

    attempt = MathAttempt(
        problem_id=req.problem_id, grade=req.grade, unit=req.unit,
        lesson=req.lesson, stage="try", is_correct=is_correct,
        user_answer=req.user_answer[:200],
        error_type="none" if is_correct else "concept_gap",
        time_spent_sec=req.time_spent_sec,
        attempted_at=now,
    )
    db.add(attempt)

    if not is_correct:
        wr = db.query(MathWrongReview).filter_by(problem_id=req.problem_id, is_mastered=False).first()
        if not wr:
            wr = MathWrongReview(
                problem_id=req.problem_id,
                next_review_date=(datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
                interval_days=1,
                source_stage="try",
                attempt_count=1,
                consecutive_correct=0,
            )
            db.add(wr)
            db.flush()
            wr.original_attempt_id = attempt.id
        else:
            wr.source_stage = "try"
            wr.attempt_count = (wr.attempt_count or 0) + 1
            wr.consecutive_correct = 0
    else:
        wr = db.query(MathWrongReview).filter_by(problem_id=req.problem_id, is_mastered=False).first()
        if wr:
            wr.consecutive_correct = (wr.consecutive_correct or 0) + 1
            if wr.consecutive_correct >= 2:
                wr.is_mastered = True

    # 2-stage feedback text
    fb = problem.get("feedback", {})
    if is_correct:
        feedback_stage = "correct"
        feedback_text = (fb.get("correct", "") if isinstance(fb, dict) else "") or "Keep it up!"
    elif req.attempt_number >= 2:
        feedback_stage = "second_wrong"
        feedback_text = (fb.get("second_wrong", fb.get("misconception", "")) if isinstance(fb, dict) else "") or f"The answer is {correct_display}. Let's understand why."
    else:
        feedback_stage = "first_wrong"
        feedback_text = (fb.get("first_wrong", fb.get("incorrect", "")) if isinstance(fb, dict) else "") or "Try again — think it through."

    db.commit()

    return {
        "is_correct": is_correct,
        "correct_answer": correct_display,
        "feedback_stage": feedback_stage,
        "feedback": feedback_text,
        "cpa_hint": problem.get("cpa_hint") if feedback_stage == "second_wrong" else None,
        "solution_steps": problem.get("solution_steps", []) if not is_correct else [],
    }


# @tag MATH @tag ACADEMY
@router.post("/api/math/academy/exit-quiz/submit")
def submit_exit_quiz(req: ExitQuizSubmitIn, db: Session = Depends(get_db)):
    """Submit exit quiz (batch, 5 questions). ≥80% → complete + spaced review; <80% → retry (max 3) (v2.0)."""
    now = datetime.now().isoformat()
    today = datetime.now().date()

    data = _load_lesson_json(req.grade, req.unit, req.lesson)
    # Determine which attempt this is (pre-increment: current attempt = stored + 1)
    _prog_for_attempt = db.query(MathProgress).filter_by(grade=req.grade, unit=req.unit, lesson=req.lesson).first()
    _current_attempt = ((_prog_for_attempt.exit_quiz_attempts or 0) + 1) if _prog_for_attempt else 1
    eq_problems = _stage_problems(data, "exit_quiz", exit_quiz_attempt=_current_attempt)
    problems_by_id = {p.get("id"): p for p in eq_problems}

    correct_count = 0
    results = []
    for ans in req.answers:
        problem = problems_by_id.get(ans.problem_id)
        if not problem:
            results.append({"problem_id": ans.problem_id, "is_correct": False, "correct_answer": "", "error": "not_found"})
            continue

        is_correct, correct_display = _grade_answer(problem, ans.user_answer)
        if is_correct:
            correct_count += 1

        attempt = MathAttempt(
            problem_id=ans.problem_id, grade=req.grade, unit=req.unit,
            lesson=req.lesson, stage="exit_quiz", is_correct=is_correct,
            user_answer=ans.user_answer[:200],
            error_type="none" if is_correct else "concept_gap",
            time_spent_sec=ans.time_spent_sec,
            attempted_at=now,
        )
        db.add(attempt)

        if not is_correct:
            wr = db.query(MathWrongReview).filter_by(problem_id=ans.problem_id, is_mastered=False).first()
            if not wr:
                wr = MathWrongReview(
                    problem_id=ans.problem_id,
                    next_review_date=(today + timedelta(days=1)).strftime("%Y-%m-%d"),
                    interval_days=1,
                    source_stage="exit_quiz",
                    attempt_count=1,
                    consecutive_correct=0,
                )
                db.add(wr)
                db.flush()
                wr.original_attempt_id = attempt.id
            else:
                wr.source_stage = "exit_quiz"
                wr.attempt_count = (wr.attempt_count or 0) + 1
                wr.consecutive_correct = 0

        results.append({"problem_id": ans.problem_id, "is_correct": is_correct, "correct_answer": correct_display})

    total = len(req.answers) or 1
    pct = correct_count / total * 100
    passed = pct >= 80

    prog = db.query(MathProgress).filter_by(grade=req.grade, unit=req.unit, lesson=req.lesson).first()
    if not prog:
        prog = MathProgress(grade=req.grade, unit=req.unit, lesson=req.lesson, last_accessed=now)
        db.add(prog)

    prog.exit_quiz_score = correct_count
    prog.exit_quiz_attempts = (prog.exit_quiz_attempts or 0) + 1
    prog.last_accessed = now

    next_review_date = None
    xp_earned = 0
    force_unlocked = False

    if passed:
        prog.exit_quiz_passed = True
        prog.is_completed = True
        prog.stage = "completed"
        prog.completed_at = now

        intervals = _spaced_schedule(pct)
        review_date = (today + timedelta(days=intervals[0])).strftime("%Y-%m-%d")
        next_review_date = review_date
        lesson_id = f"{req.grade}/{req.unit}/{req.lesson}"

        existing_sr = db.query(MathSpacedReview).filter_by(lesson_id=lesson_id, grade=req.grade).first()
        if not existing_sr:
            db.add(MathSpacedReview(
                lesson_id=lesson_id, unit_id=req.unit, grade=req.grade,
                exit_quiz_score=correct_count,
                next_review_date=review_date,
                interval_days=intervals[0],
                interval_index=0,
                created_at=now,
            ))
        else:
            existing_sr.exit_quiz_score = correct_count
            existing_sr.next_review_date = review_date
            existing_sr.interval_days = intervals[0]
            existing_sr.interval_index = 0

        try:
            xp_engine.award_xp(db, "math_lesson_complete", detail=lesson_id)
            xp_earned = xp_engine.get_xp_rules(db).get("math_lesson_complete", 10)
        except Exception as e:
            logger.warning("XP award failed: %s", e)
        try:
            streak_engine.mark_math_done(db)
        except Exception as e:
            logger.warning("Streak math mark failed: %s", e)
    elif (prog.exit_quiz_attempts or 0) >= 3:
        # Force unlock after 3 failed attempts
        prog.is_completed = True
        prog.stage = "completed"
        prog.completed_at = now
        force_unlocked = True

    db.commit()

    island = {"xp_multiplier": 1.0}
    if passed:
        try:
            from backend.services import island_care_engine as _care
            island = _care.apply_subject_gain(db, "math", "math_lesson")
        except Exception:
            pass

    unit_test_ready = False
    if passed:
        try:
            unit_test_path = _DATA_DIR / req.grade / req.unit / "unit_test.json"
            if unit_test_path.exists():
                all_lesson_names = [l for l in _list_json_files(_DATA_DIR / req.grade / req.unit) if l != "unit_test"]
                if all_lesson_names:
                    done_count = db.query(MathProgress).filter(
                        MathProgress.grade == req.grade,
                        MathProgress.unit == req.unit,
                        MathProgress.is_completed == True,
                    ).count()
                    unit_test_ready = done_count >= len(all_lesson_names)
        except Exception:
            pass

    return {
        "status": "ok",
        "passed": passed,
        "score": correct_count,
        "total": total,
        "pct": round(pct, 1),
        "results": results,
        "exit_quiz_attempts": prog.exit_quiz_attempts,
        "next_review_date": next_review_date,
        "xp_earned": xp_earned,
        "island": island,
        "force_unlocked": force_unlocked,
        "unit_test_ready": unit_test_ready,
    }


# ── Spaced Review ─────────────────────────────────────────────────────────────

def _unit_number(unit_id: str) -> int:
    """Extract numeric unit index from a unit id string (e.g. 'U4_...' → 4)."""
    m = re.search(r"[Uu](\d+)", unit_id or "")
    return int(m.group(1)) if m else 0


def _lesson_name(lesson_id: str) -> str:
    """Extract just the lesson file name from a lesson_id.

    lesson_id is stored as 'grade/unit/lesson' (e.g. 'G3/U1_place_value/L1_multiply').
    _load_lesson_json expects only the lesson segment.
    """
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


def _weakness_score(sr: MathSpacedReview, db: Session) -> int:
    """Weakness score = (100 - exit_quiz_pct) + wrong_review_count × 10."""
    eq_pct = int(round((sr.exit_quiz_score / 5) * 100)) if sr.exit_quiz_score else 50
    wc = (
        db.query(func.count(MathWrongReview.id))
        .filter(MathWrongReview.problem_id.like(f"%{sr.lesson_id}%"))
        .scalar()
        or 0
    )
    return max(0, 100 - eq_pct) + wc * 10


def _build_sr_problem(p: dict, lesson_id: str, unit_id: str, grade: str, title: str) -> dict:
    """Serialize a problem dict for spaced review response (includes answer for client feedback)."""
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


class SpacedReviewAnswerIn(BaseModel):
    """Single answer within a spaced review submission."""
    lesson_id: str = Field(..., max_length=80)
    unit_id: str = Field(..., max_length=80)
    grade: str = Field(..., max_length=10)
    problem_id: str = Field(..., max_length=80)
    user_answer: str = Field("", max_length=200)


class SpacedReviewSubmitIn(BaseModel):
    """Batch spaced review submission."""
    answers: list[SpacedReviewAnswerIn] = Field(..., max_length=50)


# @tag MATH @tag REVIEW
@router.get("/api/math/spaced-review/count")
def get_spaced_review_count(db: Session = Depends(get_db)) -> dict:
    """Return count of math spaced review lessons due today (for badge display)."""
    today_str = date.today().isoformat()
    count = (
        db.query(func.count(MathSpacedReview.id))
        .filter(MathSpacedReview.next_review_date <= today_str)
        .scalar()
        or 0
    )
    return {"count": int(count)}


# @tag MATH @tag REVIEW
@router.get("/api/math/spaced-review/today")
def get_spaced_review_today(db: Session = Depends(get_db)) -> dict:
    """Return all math spaced review problems due today, ordered oldest-first.

    Problem composition per lesson:
      U01-U03: 5 problems from practice_r1 pool
      U04+:    3 from current lesson + 2 interleaved from weakest prior lesson
    Includes correct answers so the client can show immediate feedback.
    """
    today_str = date.today().isoformat()

    due_lessons = (
        db.query(MathSpacedReview)
        .filter(MathSpacedReview.next_review_date <= today_str)
        .order_by(MathSpacedReview.next_review_date.asc())
        .all()
    )

    all_problems: list[dict] = []

    for sr in due_lessons:
        data = _load_lesson_json(sr.grade, sr.unit_id, _lesson_name(sr.lesson_id))
        if not data:
            continue

        current_pool = _stage_problems(data, "practice_r1") or _stage_problems(data, "exit_quiz")
        unit_num = _unit_number(sr.unit_id)
        lesson_title = data.get("title", sr.lesson_id)

        lesson_problems: list[dict] = []

        if unit_num >= 4 and len(current_pool) >= 3:
            # 3 random from current lesson
            sampled = _rng.sample(current_pool, min(3, len(current_pool)))
            for p in sampled:
                lesson_problems.append(_build_sr_problem(p, sr.lesson_id, sr.unit_id, sr.grade, lesson_title))

            # 2 interleaved from weakest prior lesson
            prior_srs = (
                db.query(MathSpacedReview)
                .filter(
                    MathSpacedReview.grade == sr.grade,
                    MathSpacedReview.id != sr.id,
                )
                .all()
            )
            earlier = [p for p in prior_srs if _unit_number(p.unit_id) < unit_num]
            if earlier:
                weakest_sr = max(earlier, key=lambda p: _weakness_score(p, db))
                w_data = _load_lesson_json(weakest_sr.grade, weakest_sr.unit_id, _lesson_name(weakest_sr.lesson_id))
                if w_data:
                    w_pool = _stage_problems(w_data, "practice_r1")
                    w_sampled = _rng.sample(w_pool, min(2, len(w_pool)))
                    for p in w_sampled:
                        lesson_problems.append(_build_sr_problem(
                            p, weakest_sr.lesson_id, weakest_sr.unit_id, weakest_sr.grade,
                            w_data.get("title", weakest_sr.lesson_id),
                        ))
        else:
            # U01-U03: 5 random from current lesson
            sampled = _rng.sample(current_pool, min(5, len(current_pool)))
            for p in sampled:
                lesson_problems.append(_build_sr_problem(p, sr.lesson_id, sr.unit_id, sr.grade, lesson_title))

        # Shuffle within each lesson's problem set for variety
        _rng.shuffle(lesson_problems)
        all_problems.extend(lesson_problems)

    return {
        "count": len(all_problems),
        "lesson_count": len(due_lessons),
        "problems": all_problems,
    }


# @tag MATH @tag REVIEW
@router.post("/api/math/spaced-review/submit")
def submit_spaced_review(req: SpacedReviewSubmitIn, db: Session = Depends(get_db)) -> dict:
    """Grade batch spaced review answers, reschedule each lesson, and award XP once.

    Miss penalty (applied to next interval):
      1 day overdue  → interval × 0.7
      2+ days overdue → reset to first interval in schedule
    """
    today = date.today()
    today_str = today.isoformat()
    now = datetime.now().isoformat()

    results: list[dict] = []
    lessons_seen: dict[str, tuple[str, str, str]] = {}  # key → (grade, unit_id, lesson_id)

    for ans in req.answers:
        data = _load_lesson_json(ans.grade, ans.unit_id, _lesson_name(ans.lesson_id))
        problem: dict | None = None
        if data:
            pool = _stage_problems(data, "practice_r1") or _stage_problems(data, "exit_quiz")
            problem = next((p for p in pool if p.get("id") == ans.problem_id), None)

        if problem:
            is_correct, correct_display = _grade_answer(problem, ans.user_answer)
        else:
            is_correct = False
            correct_display = ans.problem_id

        results.append({
            "problem_id": ans.problem_id,
            "lesson_id": ans.lesson_id,
            "is_correct": is_correct,
            "correct_answer": correct_display,
        })
        key = f"{ans.grade}|{ans.unit_id}|{ans.lesson_id}"
        lessons_seen[key] = (ans.grade, ans.unit_id, ans.lesson_id)

    # Compute per-lesson accuracy from graded results
    lesson_correct: dict[str, int] = {}
    lesson_total: dict[str, int] = {}
    for r in results:
        lid = r["lesson_id"]
        lesson_total[lid] = lesson_total.get(lid, 0) + 1
        if r["is_correct"]:
            lesson_correct[lid] = lesson_correct.get(lid, 0) + 1

    updated_lessons: list[dict] = []
    for key, (grade, unit_id, lesson_id) in lessons_seen.items():
        sr = (
            db.query(MathSpacedReview)
            .filter_by(grade=grade, unit_id=unit_id, lesson_id=lesson_id)
            .first()
        )
        if not sr:
            continue

        # Days overdue for miss penalty
        days_overdue = 0
        try:
            due_date = date.fromisoformat(sr.next_review_date)
            days_overdue = max(0, (today - due_date).days)
        except Exception:
            pass

        intervals = _spaced_schedule(
            int(round((sr.exit_quiz_score / 5) * 100)) if sr.exit_quiz_score else 50
        )

        # Review accuracy gates interval advancement:
        #   ≥80% correct → advance to next interval
        #   <80% correct → reset to first interval (re-study needed)
        l_total = lesson_total.get(lesson_id, 0)
        l_correct = lesson_correct.get(lesson_id, 0)
        review_pct = (l_correct / l_total * 100) if l_total else 0

        if review_pct >= 80:
            next_idx = min((sr.interval_index or 0) + 1, len(intervals) - 1)
        else:
            next_idx = 0

        base_interval = intervals[next_idx]

        if days_overdue == 1:
            adjusted = max(1, int(base_interval * 0.7))
        elif days_overdue >= 2:
            adjusted = intervals[0]
            next_idx = 0
        else:
            adjusted = base_interval

        sr.interval_days = adjusted
        sr.interval_index = next_idx
        sr.next_review_date = (today + timedelta(days=adjusted)).isoformat()
        sr.last_reviewed_at = now

        updated_lessons.append({
            "lesson_id": lesson_id,
            "next_review_date": sr.next_review_date,
            "interval_days": adjusted,
            "review_accuracy": round(review_pct, 1),
        })

    xp_earned = 0
    try:
        xp_earned = xp_engine.award_xp(db, "math_spaced_review")
    except Exception as e:
        logger.warning("Spaced review XP award failed: %s", e)

    db.commit()

    return {
        "status": "ok",
        "results": results,
        "lessons_updated": updated_lessons,
        "xp_earned": xp_earned,
    }
