"""
routers/math_academy_submit.py — Math Academy answer submission & lesson completion
Section: Math
Dependencies: models.py (MathProgress, MathAttempt, MathWrongReview),
              math_academy.py (_load_lesson_json, _stage_problems),
              services/xp_engine.py, services/streak_engine.py
API: POST /api/math/academy/submit-answer,
     POST /api/math/academy/complete-lesson,
     POST /api/math/academy/unit-test/submit
"""

import logging
import re
from datetime import datetime, timedelta
from fractions import Fraction
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

try:
    from ..database import get_db
    from ..models import MathProgress, MathAttempt, MathWrongReview
    from ..services import xp_engine, streak_engine
    from .math_academy import _load_lesson_json, _stage_problems
except ImportError:
    from database import get_db
    from models import MathProgress, MathAttempt, MathWrongReview
    from services import xp_engine, streak_engine
    from math_academy import _load_lesson_json, _stage_problems

router = APIRouter()
logger = logging.getLogger(__name__)

# ── Answer normalization ──────────────────────────────────────

def _normalize_math_answer(s: str) -> str:
    s = (s or "").strip().lower()
    s = s.lstrip("$").rstrip("%")
    s = s.replace(",", "")
    s = re.sub(r"\s+", " ", s)
    return s

def _to_number(s: str) -> Optional[float]:
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

def _answers_equivalent(user: str, correct: str) -> bool:
    u = _normalize_math_answer(user)
    c = _normalize_math_answer(correct)
    if u == c:
        return True
    un, cn = _to_number(u), _to_number(c)
    if un is not None and cn is not None:
        return abs(un - cn) < 1e-9
    return False

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

class CompleteLessonIn(BaseModel):
    """Mark a lesson as completed."""
    grade: str
    unit: str
    lesson: str

class SubmitUnitTestIn(BaseModel):
    """Unit test result via JSON body."""
    grade: str
    unit: str
    score: int
    total: int

# ── Endpoints ────────────────────────────────────────────────

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

    is_correct = False

    if correct_raw.upper() in "ABCDEFGH" and len(correct_raw) == 1 and choices:
        correct_idx = ord(correct_raw.upper()) - 65
        if 0 <= correct_idx < len(choices):
            correct_text = choices[correct_idx]
            clean_correct = correct_text.split(")", 1)[-1].strip() if ")" in correct_text else correct_text.strip()
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
                    original_attempt_id=None,
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
        feedback_text = "Great job!" if is_correct else f"The correct answer is {correct_raw}."

    return {
        "is_correct": is_correct,
        "correct_answer": correct_raw,
        "feedback": feedback_text,
        "solution_steps": problem.get("solution_steps", []),
    }

# @tag MATH @tag ACADEMY
@router.post("/api/math/academy/complete-lesson")
async def complete_lesson(req: CompleteLessonIn, db: Session = Depends(get_db)):
    """Mark a lesson stage as complete and award XP."""
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

# @tag MATH @tag ACADEMY
@router.post("/api/math/academy/unit-test/submit")
async def submit_unit_test_body(req: SubmitUnitTestIn, db: Session = Depends(get_db)):
    """Record unit test result, award XP on pass, return weak lesson if failed."""
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
        except Exception:
            pass
    return result
