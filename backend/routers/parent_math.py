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
    from ..models.math import MathSpacedReview, MathUnitTest
except ImportError:
    from database import get_db
    from models import (MathProgress, MathAttempt, MathWrongReview,
                        MathFactFluency, MathDailyChallenge,
                        MathKangarooProgress)
    from models.math import MathSpacedReview, MathUnitTest


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
    exit_quiz_passed  = sum(1 for r in progress_rows if r.exit_quiz_passed)
    eq_pass_rate      = round(exit_quiz_passed / completed * 100, 1) if completed else 0.0

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

    # Spaced review stats
    seven_days = (date.today() + timedelta(days=7)).isoformat()
    sr_due_today   = db.query(MathSpacedReview).filter(MathSpacedReview.next_review_date <= today_str).count()
    sr_overdue     = db.query(MathSpacedReview).filter(MathSpacedReview.next_review_date < today_str).count()
    sr_upcoming_7d = db.query(MathSpacedReview).filter(
        MathSpacedReview.next_review_date > today_str,
        MathSpacedReview.next_review_date <= seven_days,
    ).count()
    sr_total       = db.query(MathSpacedReview).count()
    sr_scores      = [r.exit_quiz_score for r in db.query(MathSpacedReview).all() if r.exit_quiz_score is not None]
    sr_avg_score   = round(sum(sr_scores) / len(sr_scores) * 20, 1) if sr_scores else 0.0  # /5 * 100

    # Exit quiz history (last 10 passed lessons, newest first)
    recent_eq = sorted(
        [r for r in progress_rows if r.exit_quiz_passed and r.completed_at],
        key=lambda r: r.completed_at or "",
        reverse=True,
    )[:10]
    exit_quiz_history = [{
        "grade":        r.grade,
        "unit":         r.unit_id,
        "lesson":       r.lesson_id,
        "score":        r.exit_quiz_score,
        "attempts":     r.exit_quiz_attempts or 1,
        "completed_at": (r.completed_at or "")[:10],
    } for r in recent_eq]

    # Unit test history (last 10)
    ut_rows = (
        db.query(MathUnitTest)
        .order_by(MathUnitTest.taken_at.desc())
        .limit(10)
        .all()
    )
    unit_test_history = [{
        "unit_id":        r.unit_id,
        "grade":          r.grade,
        "attempt_number": r.attempt_number,
        "score":          r.score,
        "total":          r.total,
        "pct":            round(r.score / r.total * 100, 1) if r.total else 0,
        "passed":         r.passed,
        "taken_at":       (r.taken_at or "")[:10],
    } for r in ut_rows]

    return {
        "academy": {
            "total_lessons":     total_lessons,
            "completed":         completed,
            "pretest_passed":    pretest_passed,
            "unit_tests_passed": unit_tests_passed,
            "exit_quiz_passed":  exit_quiz_passed,
            "eq_pass_rate":      eq_pass_rate,
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
        "spaced_review": {
            "due_today":    sr_due_today,
            "overdue":      sr_overdue,
            "upcoming_7d":  sr_upcoming_7d,
            "total":        sr_total,
            "avg_score_pct": sr_avg_score,
        },
        "exit_quiz_history": exit_quiz_history,
        "unit_test_history": unit_test_history,
    }
