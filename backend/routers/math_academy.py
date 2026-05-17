"""
routers/math_academy.py — Math Academy catalog, progress, answer submission, and round control.
Section: Math
Dependencies: models/math, models/system, services/xp_engine, _math_academy_common
Split routers (registered separately in main.py):
  math_academy_lifecycle → /api/math/academy/complete-lesson, /unit-test/submit
  math_academy_flow      → /api/math/academy/pre-test/*, /learn/*, /try/*, /exit-quiz/*
  math_spaced_review     → /api/math/spaced-review/*
API endpoints (this file):
  GET  /api/math/academy/grades
  GET  /api/math/academy/{grade}/units
  GET  /api/math/academy/{grade}/{unit}/lessons
  GET  /api/math/academy/{grade}/{unit}/{lesson}/{stage}
  GET  /api/math/academy/{grade}/{unit}/unit-test
  POST /api/math/academy/submit-answer
  GET  /api/math/academy/progress/{grade}
  POST /api/math/academy/round/complete
  GET  /api/math/academy/lesson/{grade}/{unit}/{lesson}/stage
"""
import json as _json
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.routers._math_academy_common import (
    MathProgress, MathAttempt, MathWrongReview, AppConfig,
    _validate_safe_id, _safe_math_path, _load_lesson_json, _read_json_cached,
    _list_dirs, _list_json_files, _stage_problems, _get_or_create_progress,
    _answers_equivalent, _grade_answer, _decide_next_after_round,
    _diagnose_attempt,
    SubmitAnswerIn, RoundCompleteIn,
)
from datetime import datetime, timedelta

router = APIRouter()
logger = logging.getLogger(__name__)


# ── Catalog ───────────────────────────────────────────────────────────────────

# @tag MATH @tag ACADEMY
@router.get("/api/math/academy/grades")
def get_grades() -> dict:
    """List all available math grades (directory names starting with G)."""
    from backend.routers._math_academy_common import _DATA_DIR
    grades = [g for g in _list_dirs(_DATA_DIR) if g.startswith("G")]
    return {"grades": grades}


# @tag MATH @tag ACADEMY
@router.get("/api/math/academy/{grade}/units")
def get_units(grade: str) -> dict:
    """List all units for a grade."""
    grade = _validate_safe_id(grade, "grade", max_len=10)
    units = _list_dirs(_safe_math_path(grade))
    return {"grade": grade, "units": units}


# @tag MATH @tag ACADEMY
@router.get("/api/math/academy/{grade}/{unit}/lessons")
def get_lessons(grade: str, unit: str, db: Session = Depends(get_db)) -> dict:
    """List lessons for a unit with progress state; returns unit_test_unlocked flag."""
    grade = _validate_safe_id(grade, "grade", max_len=10)
    unit = _validate_safe_id(unit, "unit", max_len=80)
    lesson_names = _list_json_files(_safe_math_path(grade, unit))
    lessons = [l for l in lesson_names if l != "unit_test"]
    prog_rows = (
        db.query(MathProgress)
        .filter(MathProgress.grade == grade, MathProgress.unit == unit,
                MathProgress.lesson.in_(lessons))
        .all()
    ) if lessons else []
    prog_by_lesson = {p.lesson: p for p in prog_rows}
    result = []
    for l in lessons:
        prog = prog_by_lesson.get(l)
        result.append({
            "name": l,
            "is_completed": prog.is_completed if prog else False,
            "stage": prog.stage if prog else "pre_test",
            "pretest_skipped": prog.pretest_skipped if prog else False,
        })
    all_done = all(r["is_completed"] for r in result) if result else False
    has_unit_test = _safe_math_path(grade, unit, "unit_test.json").exists()
    tm_row = db.query(AppConfig).filter_by(key="test_mode").first()
    is_test = tm_row and tm_row.value == "true"
    return {
        "grade": grade,
        "unit": unit,
        "lessons": result,
        "unit_test_unlocked": has_unit_test and (all_done or is_test),
    }


# @tag MATH @tag ACADEMY
@router.get("/api/math/academy/{grade}/{unit}/{lesson}/{stage}")
def get_stage_problems(
    grade: str, unit: str, lesson: str, stage: str,
    db: Session = Depends(get_db),
) -> dict:
    """Return problems for a lesson stage. Supports pre_test/pretest, learn, try, exit_quiz, practice_r1/r2/r3."""
    valid_stages = {"pretest", "pre_test", "learn", "try", "exit_quiz",
                    "practice_r1", "practice_r2", "practice_r3"}
    if stage not in valid_stages:
        raise HTTPException(status_code=400, detail=f"Invalid stage: {stage}")
    grade = _validate_safe_id(grade, "grade", max_len=10)
    unit = _validate_safe_id(unit, "unit", max_len=80)
    lesson = _validate_safe_id(lesson, "lesson", max_len=80)
    data = _load_lesson_json(grade, unit, lesson)
    if not data:
        raise HTTPException(status_code=404, detail="Lesson data not found")
    attempt = 1
    if stage == "exit_quiz":
        prog = db.query(MathProgress).filter_by(grade=grade, unit=unit, lesson=lesson).first()
        attempt = (prog.exit_quiz_attempts or 0) + 1 if prog else 1
    problems = _stage_problems(data, stage, exit_quiz_attempt=attempt)
    return {
        "grade": grade, "unit": unit, "lesson": lesson, "stage": stage,
        "problems": problems, "count": len(problems),
    }


# @tag MATH @tag ACADEMY
@router.get("/api/math/academy/{grade}/{unit}/unit-test")
def get_unit_test(grade: str, unit: str) -> dict:
    """Return unit test problems with pass threshold and time limit."""
    grade = _validate_safe_id(grade, "grade", max_len=10)
    unit = _validate_safe_id(unit, "unit", max_len=80)
    path = _safe_math_path(grade, unit, "unit_test.json")
    if not path.exists():
        raise HTTPException(status_code=404, detail="Unit test not found")
    data = _read_json_cached(str(path), path.stat().st_mtime)
    problems = data.get("problems", data if isinstance(data, list) else [])
    return {
        "grade": grade, "unit": unit,
        "problems": problems, "count": len(problems),
        "pass_threshold": data.get("pass_threshold", 0.8),
        "time_limit_min": data.get("time_limit_min", 30),
    }


# @tag MATH @tag ACADEMY
@router.post("/api/math/academy/submit-answer")
def submit_answer(req: SubmitAnswerIn, db: Session = Depends(get_db)):
    """Submit an answer for a math problem, record attempt, update progress."""
    req.clean()
    now = datetime.now().isoformat()

    data = _load_lesson_json(req.grade, req.unit, req.lesson)
    stage_problems = _stage_problems(data, req.stage)
    problem = next((p for p in stage_problems if p.get("id") == req.problem_id), None)

    if not problem:
        raise HTTPException(status_code=404, detail=f"Problem {req.problem_id} not found")

    correct_raw = str(problem.get("correct_answer", problem.get("answer", ""))).strip()
    user_raw = req.user_answer.strip()
    choices = problem.get("choices", [])
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

    diag = _diagnose_attempt(problem, req.user_answer, grade=req.grade, is_correct=is_correct)
    attempt = MathAttempt(
        problem_id=req.problem_id,
        grade=req.grade,
        unit=req.unit,
        lesson=req.lesson,
        stage=req.stage,
        is_correct=is_correct,
        user_answer=req.user_answer,
        error_type=diag.get("error_type") or ("none" if is_correct else "concept_gap"),
        time_spent_sec=req.time_spent_sec,
        attempted_at=now,
        misconception_id=diag.get("misconception_id"),
        diagnostic_note=(diag.get("note") or "")[:500],
    )
    db.add(attempt)

    prog = db.query(MathProgress).filter_by(grade=req.grade, unit=req.unit, lesson=req.lesson).first()
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
        pass

    # XP not awarded per-problem — granted at lesson_complete and unit_test_pass only.
    if not is_correct:
        if req.stage != "pre_test":
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
                    source_stage=req.stage,
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
        "diagnostic": {
            "error_type": diag.get("error_type"),
            "misconception_id": diag.get("misconception_id"),
            "short_label": diag.get("short_label"),
            "note": diag.get("note"),
        } if not is_correct else None,
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


# ── Round Control ─────────────────────────────────────────────────────────────

# @tag MATH @tag ACADEMY
@router.post("/api/math/academy/round/complete")
def complete_round(req: RoundCompleteIn, db: Session = Depends(get_db)):
    """Record R1/R2/R3 round score and apply Mastery Gating to determine next stage."""
    import json as _json  # local import — avoids naming conflict with module-level _json alias
    now = datetime.now().isoformat()
    prog = _get_or_create_progress(db, req.grade, req.unit, req.lesson, last_accessed=now)

    score_attr = {
        "practice_r1": "best_score_r1",
        "practice_r2": "best_score_r2",
        "practice_r3": "best_score_r3",
    }.get(req.round)
    if score_attr:
        prev = getattr(prog, score_attr, None)
        if prev is None or req.score > prev:
            setattr(prog, score_attr, req.score)

    next_stage, mastery_skip = _decide_next_after_round(prog, req.round, req.score, req.total)

    skipped = []
    if prog.skipped_stages:
        try:
            skipped = _json.loads(prog.skipped_stages)
            if not isinstance(skipped, list):
                skipped = []
        except Exception:
            skipped = []

    if mastery_skip and "practice_r2" not in skipped:
        skipped.append("practice_r2")
    prog.skipped_stages = _json.dumps(skipped)
    prog.stage = next_stage
    prog.last_accessed = now
    db.commit()

    return {
        "status": "ok",
        "next_stage": next_stage,
        "mastery_skip_applied": mastery_skip,
        "skipped": skipped,
        "best_score_r1": prog.best_score_r1,
        "best_score_r2": prog.best_score_r2,
        "best_score_r3": prog.best_score_r3,
    }


# @tag MATH @tag ACADEMY
@router.get("/api/math/academy/lesson/{grade}/{unit}/{lesson}/stage")
def get_lesson_stage(grade: str, unit: str, lesson: str, db: Session = Depends(get_db)):
    """Return current stage and progress state for a lesson."""
    prog = db.query(MathProgress).filter_by(grade=grade, unit=unit, lesson=lesson).first()
    if not prog:
        return {
            "grade": grade, "unit": unit, "lesson": lesson,
            "stage": "pre_test", "is_completed": False,
            "exit_quiz_attempts": 0, "exit_quiz_score": None,
            "pretest_skipped": False,
        }
    return {
        "grade": grade, "unit": unit, "lesson": lesson,
        "stage": prog.stage or "pre_test",
        "is_completed": prog.is_completed,
        "exit_quiz_attempts": prog.exit_quiz_attempts or 0,
        "exit_quiz_score": prog.exit_quiz_score,
        "pretest_skipped": prog.pretest_skipped,
    }
