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
import re
from datetime import datetime, timedelta
from fractions import Fraction
from functools import lru_cache
from pathlib import Path
from typing import Optional

# @tag MATH @tag ACADEMY
MATH_UNIT_TEST_PASS_RATIO = 0.9

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
    from ..models import MathProblem, MathProgress, MathAttempt, MathWrongReview
    from ..services import xp_engine, streak_engine
except ImportError:
    from database import get_db
    from models import MathProblem, MathProgress, MathAttempt, MathWrongReview
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
def _stage_problems(data: dict, stage: str) -> list:
    """Extract stage problems from any lesson schema.

    U1 schema: top-level key per stage (data["pretest"], data["learn"], ...).
    U2 schema: single data["items"] list where each item has a "section" field.
    U8 schema: data["sections"][stage] wrapper with renamed item fields.
    """
    if stage in data and isinstance(data[stage], list):
        return [_normalize_item(it) for it in data[stage]]
    sections = data.get("sections")
    if isinstance(sections, dict) and isinstance(sections.get(stage), list):
        return [_normalize_item(it) for it in sections[stage]]
    items = data.get("items")
    if isinstance(items, list):
        return [_normalize_item(it) for it in items if it.get("section") == stage]
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
def get_stage_problems(grade: str, unit: str, lesson: str, stage: str) -> dict:
    """Return problems for a specific lesson stage.

    Stages: pretest, learn, try, practice_r1, practice_r2, practice_r3
    """
    valid_stages = {"pretest", "learn", "try", "practice_r1", "practice_r2", "practice_r3"}
    if stage not in valid_stages:
        raise HTTPException(status_code=400, detail=f"Invalid stage: {stage}")

    data = _load_lesson_json(grade, unit, lesson)
    if not data:
        raise HTTPException(status_code=404, detail="Lesson data not found")

    problems = _stage_problems(data, stage)
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
    return {"grade": grade, "unit": unit, "problems": problems, "count": len(problems)}

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

    # XP for correct answer
    if is_correct:
        try:
            xp_engine.award_xp(db, "math_problem_correct", 1, f"Math {req.problem_id}")
        except Exception as e:
            logger.warning("XP award failed: %s", e)
    else:
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
        xp_engine.award_xp(db, "math_lesson_complete", 10, f"{req.grade}/{req.unit}/{req.lesson}")
    except Exception as e:
        logger.warning("XP award failed: %s", e)
    try:
        streak_engine.mark_math_done(db)
    except Exception as e:
        logger.warning("Streak math mark failed: %s", e)
    db.commit()
    return {"status": "ok", "is_completed": True}

class SubmitUnitTestIn(BaseModel):
    """Unit test result via JSON body."""
    grade: str
    unit: str
    score: int
    total: int

@router.post("/api/math/academy/unit-test/submit")
async def submit_unit_test_body(req: SubmitUnitTestIn, db: Session = Depends(get_db)):
    pct = (req.score / req.total * 100) if req.total else 0
    passed = pct >= 90
    rows = (
        db.query(MathProgress)
        .filter_by(grade=req.grade, unit=req.unit)
        .all()
    )
    for row in rows:
        row.unit_test_score = req.score
    if passed:
        try:
            xp_engine.award_xp(db, "math_unit_test_pass", 15, f"{req.grade}/{req.unit}")
        except Exception as e:
            logger.warning("XP award failed: %s", e)
        try:
            streak_engine.mark_math_done(db)
        except Exception as e:
            logger.warning("Streak math mark failed: %s", e)
    db.commit()
    result = {
        "status": "ok", "passed": passed,
        "score": req.score, "total": req.total,
        "pct": round(pct, 1),
    }
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
