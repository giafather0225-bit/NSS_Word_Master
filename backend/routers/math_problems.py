"""
routers/math_problems.py — My Problems (Wrong Review) API
Section: Math
Dependencies: models.py (MathWrongReview, MathAttempt)
API: GET /api/math/my-problems/summary, GET /api/math/my-problems/review,
     POST /api/math/my-problems/submit-answer
"""

import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

try:
    from ..database import get_db
    from ..models import MathWrongReview, MathAttempt
except ImportError:
    from database import get_db
    from models import MathWrongReview, MathAttempt

router = APIRouter()
logger = logging.getLogger(__name__)

# Spaced repetition intervals
_INTERVALS = [1, 3, 7, 21]


# ── Endpoints ────────────────────────────────────────────────

# @tag MATH @tag MY_PROBLEMS
@router.get("/api/math/my-problems/summary")
def problems_summary(db: Session = Depends(get_db)):
    """Return summary of wrong review items."""
    today = datetime.now().strftime("%Y-%m-%d")
    total = db.query(MathWrongReview).filter_by(is_mastered=False).count()
    due_today = (
        db.query(MathWrongReview)
        .filter(MathWrongReview.is_mastered == False, MathWrongReview.next_review_date <= today)
        .count()
    )
    mastered = db.query(MathWrongReview).filter_by(is_mastered=True).count()
    return {
        "total_pending": total,
        "due_today": due_today,
        "mastered": mastered,
    }


# @tag MATH @tag MY_PROBLEMS
@router.get("/api/math/my-problems/review")
def problems_review(db: Session = Depends(get_db)):
    """Return problems due for review today."""
    today = datetime.now().strftime("%Y-%m-%d")
    rows = (
        db.query(MathWrongReview)
        .filter(MathWrongReview.is_mastered == False, MathWrongReview.next_review_date <= today)
        .limit(20)
        .all()
    )
    return {
        "items": [
            {
                "id": r.id,
                "problem_id": r.problem_id,
                "times_reviewed": r.times_reviewed,
                "interval_days": r.interval_days,
            }
            for r in rows
        ]
    }


# @tag MATH @tag MY_PROBLEMS
@router.post("/api/math/my-problems/submit-answer")
def submit_review_answer(review_id: int, is_correct: bool, db: Session = Depends(get_db)):
    """Submit answer for a review problem. Phase 1: 1 correct = mastered."""
    row = db.query(MathWrongReview).filter_by(id=review_id).first()
    if not row:
        return {"error": "Review item not found"}

    row.times_reviewed += 1

    if is_correct:
        row.is_mastered = True
    else:
        # Advance to next interval
        idx = _INTERVALS.index(row.interval_days) if row.interval_days in _INTERVALS else 0
        next_idx = min(idx + 1, len(_INTERVALS) - 1)
        row.interval_days = _INTERVALS[next_idx]
        row.next_review_date = (
            datetime.now() + timedelta(days=row.interval_days)
        ).strftime("%Y-%m-%d")

    db.commit()
    return {
        "is_mastered": row.is_mastered,
        "next_review_date": row.next_review_date if not row.is_mastered else None,
    }
