"""
routers/math_academy_lifecycle.py — Math Academy lesson completion and unit test submission.
Section: Math
Dependencies: models/math, models/system, services/xp_engine, services/streak_engine, _math_academy_common
API endpoints:
  POST /api/math/academy/complete-lesson
  POST /api/math/academy/unit-test/submit
"""
import logging
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends

from backend.database import get_db
from backend.routers._math_academy_common import (
    MathProgress, MathAttempt, MathUnitTest, AppConfig,
    _validate_safe_id, _safe_math_path, _read_json_cached,
    _get_or_create_progress,
    CompleteLessonIn, SubmitUnitTestIn,
    xp_engine, streak_engine,
)

router = APIRouter()
logger = logging.getLogger(__name__)


# @tag MATH @tag ACADEMY @tag XP @tag STREAK
@router.post("/api/math/academy/complete-lesson")
async def complete_lesson(req: CompleteLessonIn, db: Session = Depends(get_db)):
    """Mark a lesson complete, award XP, and trigger streak + island updates."""
    _validate_safe_id(req.grade, "grade", max_len=10)
    _validate_safe_id(req.unit, "unit", max_len=80)
    _validate_safe_id(req.lesson, "lesson", max_len=80)

    prog = db.query(MathProgress).filter_by(grade=req.grade, unit=req.unit, lesson=req.lesson).first()
    if not prog:
        prog = MathProgress(
            grade=req.grade, unit=req.unit, lesson=req.lesson,
            stage="complete", is_completed=True,
        )
        db.add(prog)
    else:
        prog.is_completed = True
        prog.stage = "complete"

    try:
        xp_engine.award_xp(
            db, "math_lesson_complete",
            detail=f"{req.grade}/{req.unit}/{req.lesson}", commit=False,
        )
    except Exception as e:
        logger.warning("XP award failed: %s", e)

    db.commit()

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


# @tag MATH @tag ACADEMY @tag XP @tag STREAK
@router.post("/api/math/academy/unit-test/submit")
async def submit_unit_test_body(req: SubmitUnitTestIn, db: Session = Depends(get_db)):
    """Grade unit test, update progress rows, award XP on pass, identify weak lesson."""
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

    rows = db.query(MathProgress).filter_by(grade=req.grade, unit=req.unit).all()
    for row in rows:
        row.unit_test_score = req.score
        if passed:
            row.unit_test_passed = True

    _xp_awarded = 0
    if passed:
        try:
            _xp_awarded = xp_engine.award_xp(
                db, "math_unit_test_pass",
                detail=f"{req.grade}/{req.unit}", commit=False,
            )
        except Exception as e:
            logger.warning("XP award failed: %s", e)

    try:
        _attempt_num = (
            db.query(MathUnitTest)
            .filter_by(grade=req.grade, unit_id=req.unit)
            .count() + 1
        )
        db.add(MathUnitTest(
            unit_id=req.unit, grade=req.grade,
            attempt_number=_attempt_num, score=req.score, total=req.total,
            passed=passed, xp_awarded=_xp_awarded,
            taken_at=datetime.now().isoformat(),
        ))
    except Exception as e:
        logger.warning("MathUnitTest record failed: %s", e)

    db.commit()

    if passed:
        try:
            streak_engine.mark_math_done(db)
        except Exception as e:
            logger.warning("Streak math mark failed: %s", e)

    result = {
        "status": "ok", "passed": passed,
        "score": req.score, "total": req.total,
        "pct": round(pct, 1), "xp_earned": _xp_awarded,
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
            logger.debug("Weak-lesson lookup failed: %s", exc)

    return result
