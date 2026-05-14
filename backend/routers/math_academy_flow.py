"""
routers/math_academy_flow.py — Math Academy v2.0 lesson flow endpoints
Section: Math
Dependencies: math_academy.py (shared helpers), models/math.py, services/xp_engine, streak_engine
API: POST /api/math/academy/complete-lesson
     POST /api/math/academy/unit-test/submit
     POST /api/math/academy/round/complete
     GET  /api/math/academy/lesson/{grade}/{unit}/{lesson}/stage
     POST /api/math/academy/pre-test/submit
     POST /api/math/academy/learn/complete
     POST /api/math/academy/try/submit
     POST /api/math/academy/exit-quiz/submit
"""

import json as _json
import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

try:
    from ..database import get_db
    from ..models import MathProgress, MathAttempt, MathWrongReview, MathSpacedReview
    from ..models.math import MathUnitTest
    from ..services import xp_engine, streak_engine
    from ..services.math_diagnostic import diagnose as _diagnose_attempt
    from ..utils import validate_safe_id as _validate_safe_id
    from .math_academy import (
        _load_lesson_json, _stage_problems, _get_or_create_progress,
        _safe_math_path, _list_json_files, _grade_answer,
        _read_json_cached, _spaced_schedule,
    )
except ImportError:
    from database import get_db
    from models import MathProgress, MathAttempt, MathWrongReview, MathSpacedReview
    from models.math import MathUnitTest
    from services import xp_engine, streak_engine
    from services.math_diagnostic import diagnose as _diagnose_attempt
    from utils import validate_safe_id as _validate_safe_id
    from routers.math_academy import (
        _load_lesson_json, _stage_problems, _get_or_create_progress,
        _safe_math_path, _list_json_files, _grade_answer,
        _read_json_cached, _spaced_schedule,
    )

router = APIRouter()
logger = logging.getLogger(__name__)


# ── Lesson management ─────────────────────────────────────────

class CompleteLessonIn(BaseModel):
    """Mark a lesson as completed."""
    grade: str = Field(..., max_length=10)
    unit: str = Field(..., max_length=80)
    lesson: str = Field(..., max_length=80)


@router.post("/api/math/academy/complete-lesson")
async def complete_lesson(req: CompleteLessonIn, db: Session = Depends(get_db)):
    """Mark a lesson complete, award XP, and mark streak. @tag MATH @tag ACADEMY"""
    _validate_safe_id(req.grade, "grade", max_len=10)
    _validate_safe_id(req.unit, "unit", max_len=80)
    _validate_safe_id(req.lesson, "lesson", max_len=80)

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

    # Atomic write: progress + XP in one transaction, then streak after commit.
    # award_xp(commit=False) avoids splitting this into multiple sub-commits.
    try:
        xp_engine.award_xp(
            db, "math_lesson_complete",
            detail=f"{req.grade}/{req.unit}/{req.lesson}",
            commit=False,
        )
    except Exception as e:
        logger.warning("XP award failed: %s", e)

    db.commit()

    # Streak mark + island gain are independent side-effects, run after commit.
    try:
        streak_engine.mark_math_done(db)
    except Exception as e:
        logger.warning("Streak math mark failed: %s", e)

    island = {"xp_multiplier": 1.0}
    try:
        from backend.services import island_care_engine as _care
        island = _care.apply_subject_gain(db, "math", "math_lesson")
    except Exception:
        pass
    return {"status": "ok", "is_completed": True, "island": island}


class SubmitUnitTestIn(BaseModel):
    """Unit test result via JSON body."""
    grade: str = Field(..., max_length=10)
    unit: str = Field(..., max_length=80)
    score: int = Field(..., ge=0)
    total: int = Field(..., ge=1)


@router.post("/api/math/academy/unit-test/submit")
async def submit_unit_test_body(req: SubmitUnitTestIn, db: Session = Depends(get_db)):
    """Submit unit test score, update progress, and award XP if passed. @tag MATH @tag ACADEMY"""
    pct = (req.score / req.total * 100) if req.total else 0
    unit_path = _safe_math_path(req.grade, req.unit, "unit_test.json")
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
            # commit=False: keep MathProgress updates + XP + MathUnitTest in one transaction.
            _xp_awarded = xp_engine.award_xp(
                db, "math_unit_test_pass",
                detail=f"{req.grade}/{req.unit}",
                commit=False,
            )
        except Exception as e:
            logger.warning("XP award failed: %s", e)
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
    # mark_math_done after commit: avoids premature inner commit breaking atomicity above.
    if passed:
        try:
            streak_engine.mark_math_done(db)
        except Exception as e:
            logger.warning("Streak math mark failed: %s", e)
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
            logger.debug(
                "Weak-lesson lookup failed for grade=%s unit=%s: %s",
                req.grade, req.unit, exc,
            )
    return result


# ════════════════════════════════════════════════════════════
#  MATH_SPEC v2.0 — pre_test → learn → try → exit_quiz flow
# ════════════════════════════════════════════════════════════

def _decide_next_after_round(
    prog: "MathProgress",
    current_round: str,
    score: int,
    total: int,
) -> tuple[str, bool]:
    """Mastery Gating 결정.

    규칙
    - R1 perfect (100%) AND PT mastery (PT 100%) → R2 skip → R3 직행
    - 그 외 정상 진행: R1 → R2 → R3 → complete
    - R3 직접 완료 시 → complete (XP는 complete-lesson에서 별도 처리)

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


# ── v2.0 Pydantic schemas ─────────────────────────────────────

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
    attempt_number: int = 1  # 1 = first attempt, 2 = retry (2-stage feedback)


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
    """라운드(R1/R2/R3) 완료 보고 — Mastery Gating용."""
    grade: str = Field(..., max_length=10)
    unit: str = Field(..., max_length=80)
    lesson: str = Field(..., max_length=80)
    round: str = Field(..., max_length=20)
    score: int = Field(..., ge=0)
    total: int = Field(..., ge=1)


# ── v2.0 Endpoints ────────────────────────────────────────────

@router.post("/api/math/academy/round/complete")
def complete_round(req: RoundCompleteIn, db: Session = Depends(get_db)):
    """라운드 완료 보고 — best_score 갱신 + Mastery Gating 적용된 next_stage 반환. @tag MATH @tag ACADEMY

    프론트엔드 흐름
    1) R1 5/5 풀고 → POST /round/complete {round:"practice_r1", score:5, total:5}
    2) 응답: {next_stage:"practice_r3", mastery_skip_applied:true, skipped:["practice_r2"]}
    3) 프론트엔드는 R2 화면을 건너뛰고 R3로 이동
    """
    now = datetime.now().isoformat()
    prog = _get_or_create_progress(db, req.grade, req.unit, req.lesson, last_accessed=now)
    # best_score 갱신 (이전보다 높을 때만)
    score_attr = {
        "practice_r1": "best_score_r1",
        "practice_r2": "best_score_r2",
        "practice_r3": "best_score_r3",
    }.get(req.round)
    if score_attr:
        prev = getattr(prog, score_attr, None)
        if prev is None or req.score > prev:
            setattr(prog, score_attr, req.score)
    # 다음 stage 결정
    next_stage, mastery_skip = _decide_next_after_round(prog, req.round, req.score, req.total)
    # skipped_stages 추적
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


@router.get("/api/math/academy/lesson/{grade}/{unit}/{lesson}/stage")
def get_lesson_stage(grade: str, unit: str, lesson: str, db: Session = Depends(get_db)):
    """Return current stage for lesson resume (v2.0). @tag MATH @tag ACADEMY"""
    prog = db.query(MathProgress).filter_by(grade=grade, unit=unit, lesson=lesson).first()
    if not prog:
        return {
            "grade": grade, "unit": unit, "lesson": lesson,
            "stage": "pre_test", "is_completed": False,
            "exit_quiz_attempts": 0, "exit_quiz_score": None, "pretest_skipped": False,
        }
    stage = prog.stage or "pre_test"
    return {
        "grade": grade, "unit": unit, "lesson": lesson,
        "stage": stage,
        "is_completed": prog.is_completed,
        "exit_quiz_attempts": prog.exit_quiz_attempts or 0,
        "exit_quiz_score": prog.exit_quiz_score,
        "pretest_skipped": prog.pretest_skipped,
    }


@router.post("/api/math/academy/pre-test/submit")
def submit_pre_test(req: PreTestSubmitIn, db: Session = Depends(get_db)):
    """Record pre-test diagnostic result and advance stage to 'learn' (v2.0). @tag MATH @tag ACADEMY

    Pre-test is diagnostic only — stage always advances to 'learn' regardless of score.
    """
    now = datetime.now().isoformat()
    prog = _get_or_create_progress(db, req.grade, req.unit, req.lesson, last_accessed=now)

    pct = (req.score / req.total * 100) if req.total else 0
    prog.pretest_score = req.score
    prog.pretest_passed = pct >= 80
    prog.pretest_skipped = req.skipped
    # Mastery Gating: PT 만점이면 R2 면제 자격 부여 (R1 후 최종 결정)
    prog.pretest_mastery = (pct >= 100.0)
    prog.stage = "learn"
    prog.last_accessed = now
    db.commit()

    # 권장 학습 경로 — PT 만점 시 R2 미리 면제 안내 (R1 결과로 확정)
    if prog.pretest_mastery:
        recommended_path = ["learn", "try", "practice_r1", "practice_r3"]
    else:
        recommended_path = ["learn", "try", "practice_r1", "practice_r2", "practice_r3"]

    return {
        "status": "ok",
        "next_stage": "learn",
        "score": req.score,
        "total": req.total,
        "pct": round(pct, 1),
        "passed": prog.pretest_passed,
        # Mastery Gating
        "mastery": prog.pretest_mastery,
        "recommended_path": recommended_path,
    }


@router.post("/api/math/academy/learn/complete")
def complete_learn_stage(req: LearnCompleteIn, db: Session = Depends(get_db)):
    """Mark learn stage complete and advance to 'try' (v2.0). @tag MATH @tag ACADEMY"""
    now = datetime.now().isoformat()
    prog = _get_or_create_progress(db, req.grade, req.unit, req.lesson, stage="try", last_accessed=now)
    prog.stage = "try"
    prog.last_accessed = now
    db.commit()
    return {"status": "ok", "next_stage": "try"}


@router.post("/api/math/academy/try/submit")
def submit_try(req: TrySubmitIn, db: Session = Depends(get_db)):
    """Submit a single try-stage answer with 2-stage feedback (v2.0). @tag MATH @tag ACADEMY

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

    diag = _diagnose_attempt(problem, req.user_answer, grade=req.grade, is_correct=is_correct)
    attempt = MathAttempt(
        problem_id=req.problem_id, grade=req.grade, unit=req.unit,
        lesson=req.lesson, stage="try", is_correct=is_correct,
        user_answer=req.user_answer[:200],
        error_type=diag.get("error_type") or ("none" if is_correct else "concept_gap"),
        time_spent_sec=req.time_spent_sec,
        attempted_at=now,
        misconception_id=diag.get("misconception_id"),
        diagnostic_note=(diag.get("note") or "")[:500],
    )
    db.add(attempt)

    if not is_correct:
        # Lookup any existing row (mastered or not) — UNIQUE(problem_id) means only one can exist.
        wr = db.query(MathWrongReview).filter_by(problem_id=req.problem_id).first()
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

    # 2-stage feedback text
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


@router.post("/api/math/academy/exit-quiz/submit")
def submit_exit_quiz(req: ExitQuizSubmitIn, db: Session = Depends(get_db)):
    """Submit exit quiz (batch, 5 questions). ≥80% → complete + spaced review; <80% → retry (max 3) (v2.0). @tag MATH @tag ACADEMY"""
    from datetime import date as _date
    now = datetime.now().isoformat()
    today = datetime.now().date()

    data = _load_lesson_json(req.grade, req.unit, req.lesson)
    # Determine which attempt this is (pre-increment: current attempt = stored + 1)
    _prog_for_attempt = db.query(MathProgress).filter_by(
        grade=req.grade, unit=req.unit, lesson=req.lesson,
    ).first()
    _current_attempt = ((_prog_for_attempt.exit_quiz_attempts or 0) + 1) if _prog_for_attempt else 1
    eq_problems = _stage_problems(data, "exit_quiz", exit_quiz_attempt=_current_attempt)
    problems_by_id = {p.get("id"): p for p in eq_problems}

    correct_count = 0
    results = []
    for ans in req.answers:
        problem = problems_by_id.get(ans.problem_id)
        if not problem:
            results.append({
                "problem_id": ans.problem_id,
                "is_correct": False,
                "correct_answer": "",
                "error": "not_found",
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
            time_spent_sec=ans.time_spent_sec,
            attempted_at=now,
            misconception_id=diag.get("misconception_id"),
            diagnostic_note=(diag.get("note") or "")[:500],
        )
        db.add(attempt)

        if not is_correct:
            # Lookup any existing row (mastered or not) — UNIQUE(problem_id) means only one can exist.
            wr = db.query(MathWrongReview).filter_by(problem_id=ans.problem_id).first()
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
                        MathProgress.is_completed == True,  # noqa: E712
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
