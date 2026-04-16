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
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

try:
    from ..database import get_db
    from ..models import MathProblem, MathProgress, MathAttempt, MathWrongReview
    from ..services import xp_engine
except ImportError:
    from database import get_db
    from models import MathProblem, MathProgress, MathAttempt, MathWrongReview
    from services import xp_engine

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
def _load_lesson_json(grade: str, unit: str, lesson: str) -> dict:
    """Load a lesson JSON file from data/math/{grade}/{unit}/{lesson}.json."""
    path = _DATA_DIR / grade / unit / f"{lesson}.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text("utf-8"))


# @tag MATH @tag ACADEMY
def _list_dirs(parent: Path) -> list[str]:
    """List sorted subdirectory names under parent."""
    if not parent.is_dir():
        return []
    return sorted(
        d.name for d in parent.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    )


# @tag MATH @tag ACADEMY
def _list_json_files(parent: Path) -> list[str]:
    """List sorted JSON filenames (without .json) under parent."""
    if not parent.is_dir():
        return []
    return sorted(
        f.stem for f in parent.iterdir()
        if f.suffix == ".json" and not f.name.startswith(".")
    )


# ── Endpoints ────────────────────────────────────────────────

# @tag MATH @tag ACADEMY
@router.get("/api/math/academy/grades")
def get_grades():
    """Return available grade folders (e.g., G3, G4, G5, G6)."""
    grades = [g for g in _list_dirs(_DATA_DIR) if g.startswith("G")]
    return {"grades": grades}


# @tag MATH @tag ACADEMY
@router.get("/api/math/academy/{grade}/units")
def get_units(grade: str):
    """Return available units for a grade."""
    units = _list_dirs(_DATA_DIR / grade)
    return {"grade": grade, "units": units}


# @tag MATH @tag ACADEMY
@router.get("/api/math/academy/{grade}/{unit}/lessons")
def get_lessons(grade: str, unit: str, db: Session = Depends(get_db)):
    """Return available lessons for a unit, with progress info."""
    lesson_names = _list_json_files(_DATA_DIR / grade / unit)
    # Filter out unit_test from lesson list
    lessons = [l for l in lesson_names if l != "unit_test"]

    result = []
    for l in lessons:
        prog = (
            db.query(MathProgress)
            .filter_by(grade=grade, unit=unit, lesson=l)
            .first()
        )
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
def get_stage_problems(grade: str, unit: str, lesson: str, stage: str):
    """Return problems for a specific lesson stage.

    Stages: pretest, learn, try, practice_r1, practice_r2, practice_r3
    """
    valid_stages = {"pretest", "learn", "try", "practice_r1", "practice_r2", "practice_r3"}
    if stage not in valid_stages:
        raise HTTPException(status_code=400, detail=f"Invalid stage: {stage}")

    data = _load_lesson_json(grade, unit, lesson)
    if not data:
        raise HTTPException(status_code=404, detail="Lesson data not found")

    problems = data.get(stage, [])
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
def get_unit_test(grade: str, unit: str):
    """Return unit test problems."""
    path = _DATA_DIR / grade / unit / "unit_test.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Unit test not found")
    data = json.loads(path.read_text("utf-8"))
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
    stage_problems = data.get(req.stage, [])
    problem = next((p for p in stage_problems if p.get("id") == req.problem_id), None)

    if not problem:
        raise HTTPException(status_code=404, detail=f"Problem {req.problem_id} not found")

    correct_answer = str(problem.get("answer", "")).strip()
    is_correct = req.user_answer.strip().lower() == correct_answer.lower()

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
                from datetime import timedelta
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

    return {
        "is_correct": is_correct,
        "correct_answer": correct_answer,
        "feedback": problem.get("feedback_correct" if is_correct else "feedback_wrong", ""),
        "solution_steps": problem.get("solution_steps", []),
    }


# @tag MATH @tag ACADEMY
@router.post("/api/math/academy/unit-test/submit")
def submit_unit_test(
    grade: str, unit: str, score: int, total: int,
    db: Session = Depends(get_db),
):
    """Submit unit test results."""
    passed = total > 0 and (score / total) >= 0.9

    # Update all lesson progress for this unit with unit test info
    progs = db.query(MathProgress).filter_by(grade=grade, unit=unit).all()
    for p in progs:
        p.unit_test_score = score
        p.unit_test_passed = passed

    if passed:
        try:
            xp_engine.award_xp(db, "math_unit_test_pass", 15, f"Math {grade}/{unit}")
        except Exception as e:
            logger.warning("XP award failed: %s", e)

    db.commit()

    # Find weak lesson if failed
    weak_lesson = None
    if not passed:
        # Count wrong attempts per lesson in this unit
        from sqlalchemy import func
        wrong_counts = (
            db.query(MathAttempt.lesson, func.count(MathAttempt.id))
            .filter(
                MathAttempt.grade == grade,
                MathAttempt.unit == unit,
                MathAttempt.is_correct == False,
            )
            .group_by(MathAttempt.lesson)
            .order_by(func.count(MathAttempt.id).desc())
            .first()
        )
        if wrong_counts:
            weak_lesson = wrong_counts[0]

    return {
        "passed": passed,
        "score": score,
        "total": total,
        "percentage": round(score / total * 100, 1) if total else 0,
        "weak_lesson": weak_lesson,
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
