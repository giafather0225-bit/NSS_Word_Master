"""
routers/parent_math.py — Parent Dashboard Math summary endpoint
Section: Parent
Dependencies: models.py (MathProgress, MathAttempt, MathWrongReview,
              MathFactFluency, MathDailyChallenge, MathKangarooProgress)
API: GET /api/parent/math-summary
"""

from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

try:
    from ..database import get_db
    from ..models import (MathProgress, MathAttempt, MathWrongReview,
                          MathFactFluency, MathDailyChallenge,
                          MathKangarooProgress)
except ImportError:
    from database import get_db
    from models import (MathProgress, MathAttempt, MathWrongReview,
                        MathFactFluency, MathDailyChallenge,
                        MathKangarooProgress)


router = APIRouter()


@router.get("/api/parent/math-summary")
def parent_math_summary(db: Session = Depends(get_db)):
    """Aggregated Math stats for the parent dashboard. @tag PARENT MATH"""
    # Academy progress
    progress_rows = db.query(MathProgress).all()
    total_lessons     = len(progress_rows)
    completed         = sum(1 for r in progress_rows if r.is_completed)
    pretest_passed    = sum(1 for r in progress_rows if r.pretest_passed)
    unit_tests_passed = sum(1 for r in progress_rows if r.unit_test_passed)

    # Attempts — last 7 days
    week_ago = (date.today() - timedelta(days=7)).isoformat()
    recent_attempts = (
        db.query(MathAttempt)
        .filter(MathAttempt.attempted_at >= week_ago)
        .all()
    )
    total_attempts = len(recent_attempts)
    correct_attempts = sum(1 for a in recent_attempts if a.is_correct)
    accuracy_7d = round(correct_attempts * 100 / total_attempts, 1) if total_attempts else 0.0

    # Weak concepts (top 5 by wrong count)
    concept_rows = (
        db.query(MathAttempt.lesson, func.count(MathAttempt.id).label("wrong"))
        .filter(MathAttempt.is_correct.is_(False))
        .group_by(MathAttempt.lesson)
        .order_by(func.count(MathAttempt.id).desc())
        .limit(5)
        .all()
    )
    weak_areas = [{"lesson": r.lesson, "wrong_count": r.wrong} for r in concept_rows]

    # Wrong-review queue
    today_str = date.today().isoformat()
    wrong_pending = db.query(MathWrongReview).filter(
        MathWrongReview.is_mastered.is_(False),
        MathWrongReview.next_review_date <= today_str,
    ).count()
    wrong_mastered = db.query(MathWrongReview).filter(
        MathWrongReview.is_mastered.is_(True)
    ).count()

    # Fact fluency per set
    fluency_rows = db.query(MathFactFluency).all()
    fluency = [{
        "fact_set":      r.fact_set,
        "phase":         r.current_phase,
        "best_score":    r.best_score,
        "best_time_sec": r.best_time_sec,
        "accuracy_pct":  round(r.accuracy_pct or 0, 1),
        "total_rounds":  r.total_rounds,
    } for r in fluency_rows]

    # Daily challenge — last 7 days
    daily_rows = (
        db.query(MathDailyChallenge)
        .filter(MathDailyChallenge.challenge_date >= week_ago)
        .order_by(MathDailyChallenge.challenge_date.desc())
        .all()
    )
    daily_recent = [{
        "date":      r.challenge_date,
        "score":     r.score,
        "total":     r.total,
        "completed": r.completed,
    } for r in daily_rows]

    # Kangaroo sets completed
    kang_rows = db.query(MathKangarooProgress).all()
    kangaroo = [{
        "set_id":       r.set_id,
        "score":        r.score,
        "total":        r.total,
        "completed_at": (r.completed_at or "")[:10],
    } for r in kang_rows]

    return {
        "academy": {
            "total_lessons":     total_lessons,
            "completed":         completed,
            "pretest_passed":    pretest_passed,
            "unit_tests_passed": unit_tests_passed,
        },
        "recent_7d": {
            "total_attempts":   total_attempts,
            "correct_attempts": correct_attempts,
            "accuracy_pct":     accuracy_7d,
        },
        "weak_areas":    weak_areas,
        "wrong_review":  {"pending": wrong_pending, "mastered": wrong_mastered},
        "fluency":       fluency,
        "daily_recent":  daily_recent,
        "kangaroo":      kangaroo,
    }
