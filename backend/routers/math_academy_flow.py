"""
routers/math_academy_flow.py — Math Academy per-stage submission endpoints.
Section: Math
Dependencies: models/math, services/xp_engine, services/streak_engine, _math_academy_common
API endpoints:
  POST /api/math/academy/pre-test/submit
  POST /api/math/academy/learn/complete
  POST /api/math/academy/try/submit
  POST /api/math/academy/exit-quiz/submit
"""
import logging
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException

from backend.database import get_db
from backend.routers._math_academy_common import (
    MathProgress, MathAttempt, MathWrongReview, MathSpacedReview,
    _validate_safe_id, _safe_math_path, _load_lesson_json,
    _stage_problems, _get_or_create_progress, _grade_answer, _diagnose_attempt,
    _spaced_schedule, _list_json_files,
    PreTestSubmitIn, LearnCompleteIn, TrySubmitIn, ExitQuizSubmitIn,
    xp_engine, streak_engine,
)

router = APIRouter()
logger = logging.getLogger(__name__)


# @tag MATH @tag ACADEMY
@router.post("/api/math/academy/pre-test/submit")
def submit_pre_test(req: PreTestSubmitIn, db: Session = Depends(get_db)):
    """Record pre-test score, set mastery flag, advance stage to learn."""
    now = datetime.now().isoformat()
    prog = _get_or_create_progress(db, req.grade, req.unit, req.lesson, last_accessed=now)
    pct = (req.score / req.total * 100) if req.total else 0
    prog.pretest_score = req.score
    prog.pretest_passed = pct >= 80
    prog.pretest_skipped = req.skipped
    prog.pretest_mastery = (pct >= 100.0)
    prog.stage = "learn"
    prog.last_accessed = now
    db.commit()

    if prog.pretest_mastery:
        recommended_path = ["learn", "try", "practice_r1", "practice_r3"]
    else:
        recommended_path = ["learn", "try", "practice_r1", "practice_r2", "practice_r3"]

    return {
        "status": "ok", "next_stage": "learn",
        "score": req.score, "total": req.total,
        "pct": round(pct, 1), "passed": prog.pretest_passed,
        "mastery": prog.pretest_mastery, "recommended_path": recommended_path,
    }


# @tag MATH @tag ACADEMY
@router.post("/api/math/academy/learn/complete")
def complete_learn_stage(req: LearnCompleteIn, db: Session = Depends(get_db)):
    """Advance lesson stage from learn → try."""
    now = datetime.now().isoformat()
    prog = _get_or_create_progress(db, req.grade, req.unit, req.lesson, stage="try", last_accessed=now)
    prog.stage = "try"
    prog.last_accessed = now
    db.commit()
    return {"status": "ok", "next_stage": "try"}


# @tag MATH @tag ACADEMY
@router.post("/api/math/academy/try/submit")
def submit_try(req: TrySubmitIn, db: Session = Depends(get_db)):
    """Submit a single try-stage answer; return 2-stage feedback."""
    now = datetime.now().isoformat()
    data = _load_lesson_json(req.grade, req.unit, req.lesson)
    problems = _stage_problems(data, "try")
    problem = next((p for p in problems if p.get("id") == req.problem_id), None)
    if not problem:
        raise HTTPException(status_code=404, detail=f"Problem {req.problem_id} not found in try stage")

    is_correct, correct_display = _grade_answer(problem, req.user_answer)
    diag = _diagnose_attempt(problem, req.user_answer, grade=req.grade, is_correct=is_correct)

    attempt = MathAttempt(
        problem_id=req.problem_id, grade=req.grade, unit=req.unit,
        lesson=req.lesson, stage="try", is_correct=is_correct,
        user_answer=req.user_answer[:200],
        error_type=diag.get("error_type") or ("none" if is_correct else "concept_gap"),
        time_spent_sec=req.time_spent_sec, attempted_at=now,
        misconception_id=diag.get("misconception_id"),
        diagnostic_note=(diag.get("note") or "")[:500],
    )
    db.add(attempt)

    if not is_correct:
        wr = db.query(MathWrongReview).filter_by(problem_id=req.problem_id).first()
        if not wr:
            wr = MathWrongReview(
                problem_id=req.problem_id,
                next_review_date=(datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
                interval_days=1, source_stage="try", attempt_count=1, consecutive_correct=0,
            )
            db.add(wr)
            db.flush()
            wr.original_attempt_id = attempt.id
        else:
            wr.is_mastered = False
            wr.source_stage = "try"
            wr.attempt_count = (wr.attempt_count or 0) + 1
            wr.consecutive_correct = 0
    else:
        wr = db.query(MathWrongReview).filter_by(problem_id=req.problem_id, is_mastered=False).first()
        if wr:
            wr.consecutive_correct = (wr.consecutive_correct or 0) + 1
            if wr.consecutive_correct >= 2:
                wr.is_mastered = True

    fb = problem.get("feedback", {})
    if is_correct:
        feedback_stage = "correct"
        feedback_text = (fb.get("correct", "") if isinstance(fb, dict) else "") or "Keep it up!"
    elif req.attempt_number >= 2:
        feedback_stage = "second_wrong"
        feedback_text = (
            (fb.get("second_wrong", fb.get("misconception", "")) if isinstance(fb, dict) else "")
            or f"The answer is {correct_display}. Let's understand why."
        )
    else:
        feedback_stage = "first_wrong"
        feedback_text = (
            (fb.get("first_wrong", fb.get("incorrect", "")) if isinstance(fb, dict) else "")
            or "Try again — think it through."
        )

    db.commit()

    return {
        "is_correct": is_correct,
        "correct_answer": correct_display,
        "feedback_stage": feedback_stage,
        "feedback": feedback_text,
        "cpa_hint": problem.get("cpa_hint") if feedback_stage == "second_wrong" else None,
        "solution_steps": problem.get("solution_steps", []) if not is_correct else [],
    }


# @tag MATH @tag ACADEMY @tag XP @tag STREAK
@router.post("/api/math/academy/exit-quiz/submit")
def submit_exit_quiz(req: ExitQuizSubmitIn, db: Session = Depends(get_db)):
    """Grade all exit-quiz answers, update spaced-review schedule, award XP on pass (≥80%)."""
    now = datetime.now().isoformat()
    today = datetime.now().date()

    data = _load_lesson_json(req.grade, req.unit, req.lesson)
    _prog_for_attempt = (
        db.query(MathProgress)
        .filter_by(grade=req.grade, unit=req.unit, lesson=req.lesson)
        .first()
    )
    _current_attempt = ((_prog_for_attempt.exit_quiz_attempts or 0) + 1) if _prog_for_attempt else 1
    eq_problems = _stage_problems(data, "exit_quiz", exit_quiz_attempt=_current_attempt)
    problems_by_id = {p.get("id"): p for p in eq_problems}

    correct_count = 0
    results = []
    for ans in req.answers:
        problem = problems_by_id.get(ans.problem_id)
        if not problem:
            results.append({
                "problem_id": ans.problem_id, "is_correct": False,
                "correct_answer": "", "error": "not_found",
            })
            continue

        is_correct, correct_display = _grade_answer(problem, ans.user_answer)
        if is_correct:
            correct_count += 1

        diag = _diagnose_attempt(problem, ans.user_answer, grade=req.grade, is_correct=is_correct)
        attempt = MathAttempt(
            problem_id=ans.problem_id, grade=req.grade, unit=req.unit,
            lesson=req.lesson, stage="exit_quiz", is_correct=is_correct,
            user_answer=ans.user_answer[:200],
            error_type=diag.get("error_type") or ("none" if is_correct else "concept_gap"),
            time_spent_sec=ans.time_spent_sec, attempted_at=now,
            misconception_id=diag.get("misconception_id"),
            diagnostic_note=(diag.get("note") or "")[:500],
        )
        db.add(attempt)

        if not is_correct:
            wr = db.query(MathWrongReview).filter_by(problem_id=ans.problem_id).first()
            if not wr:
                wr = MathWrongReview(
                    problem_id=ans.problem_id,
                    next_review_date=(today + timedelta(days=1)).strftime("%Y-%m-%d"),
                    interval_days=1, source_stage="exit_quiz", attempt_count=1, consecutive_correct=0,
                )
                db.add(wr)
                db.flush()
                wr.original_attempt_id = attempt.id
            else:
                wr.is_mastered = False
                wr.source_stage = "exit_quiz"
                wr.attempt_count = (wr.attempt_count or 0) + 1
                wr.consecutive_correct = 0

        results.append({
            "problem_id": ans.problem_id,
            "is_correct": is_correct,
            "correct_answer": correct_display,
        })

    total = len(req.answers) or 1
    pct = correct_count / total * 100
    passed = pct >= 80

    prog = _get_or_create_progress(db, req.grade, req.unit, req.lesson, last_accessed=now)
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
                exit_quiz_score=correct_count, next_review_date=review_date,
                interval_days=intervals[0], interval_index=0, created_at=now,
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
        except Exception as exc:
            logger.warning("Failed to apply island care gain on math lesson complete: %s", exc)

    unit_test_ready = False
    if passed:
        try:
            unit_test_path = _safe_math_path(req.grade, req.unit, "unit_test.json")
            if unit_test_path.exists():
                all_lesson_names = [
                    l for l in _list_json_files(_safe_math_path(req.grade, req.unit))
                    if l != "unit_test"
                ]
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
        "status": "ok", "passed": passed,
        "score": correct_count, "total": total,
        "pct": round(pct, 1), "results": results,
        "exit_quiz_attempts": prog.exit_quiz_attempts,
        "next_review_date": next_review_date,
        "xp_earned": xp_earned, "island": island,
        "force_unlocked": force_unlocked,
        "unit_test_ready": unit_test_ready,
    }
