"""
routers/math_problems.py — My Problems (Wrong Review) API
Section: Math
Dependencies: models.py (MathWrongReview, MathAttempt)
API: GET /api/math/my-problems/summary, GET /api/math/my-problems/review,
     POST /api/math/my-problems/submit-answer
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

try:
    from ..database import get_db
    from ..models import MathWrongReview, MathAttempt
    from ..services import xp_engine, streak_engine
except ImportError:
    from database import get_db
    from models import MathWrongReview, MathAttempt
    from services import xp_engine, streak_engine

router = APIRouter()
logger = logging.getLogger(__name__)

# Spaced repetition intervals (2 consecutive correct = mastered;
# wrong resets streak and advances interval farther out)
_INTERVALS = [1, 3, 7, 21]

_DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "math"


# ── Helpers ──────────────────────────────────────────────────

def _load_problem(attempt: MathAttempt):
    """Look up the full problem JSON from the originating lesson file."""
    if not attempt:
        return None
    lesson_file = _DATA_DIR / attempt.grade / attempt.unit / f"{attempt.lesson}.json"
    if not lesson_file.exists():
        return None
    try:
        data = json.loads(lesson_file.read_text("utf-8"))
    except Exception as e:
        logger.warning("Failed to load lesson %s: %s", lesson_file, e)
        return None
    for stage_key in ("pretest", "try", "exit_quiz", "practice_r1", "practice_r2", "practice_r3"):
        for p in data.get(stage_key, []):
            if p.get("id") == attempt.problem_id:
                return p
    return None


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
    """Return problems due for review today with full problem payload."""
    today = datetime.now().strftime("%Y-%m-%d")
    rows = (
        db.query(MathWrongReview)
        .filter(MathWrongReview.is_mastered == False, MathWrongReview.next_review_date <= today)
        .order_by(MathWrongReview.next_review_date.asc())
        .limit(20)
        .all()
    )

    # Batch-load originating attempts to avoid N+1 queries.
    attempt_ids = [r.original_attempt_id for r in rows if r.original_attempt_id]
    attempts_by_id = {}
    if attempt_ids:
        attempts_by_id = {
            a.id: a for a in db.query(MathAttempt).filter(MathAttempt.id.in_(attempt_ids)).all()
        }
    # Fallback lookup: for rows missing a resolvable attempt, grab the most
    # recent attempt per problem_id in a single query.
    fallback_problem_ids = [
        r.problem_id for r in rows
        if not r.original_attempt_id or r.original_attempt_id not in attempts_by_id
    ]
    fallback_by_problem = {}
    if fallback_problem_ids:
        recent = (
            db.query(MathAttempt)
            .filter(MathAttempt.problem_id.in_(fallback_problem_ids))
            .order_by(MathAttempt.id.desc())
            .all()
        )
        for a in recent:
            fallback_by_problem.setdefault(a.problem_id, a)

    items = []
    for r in rows:
        attempt = attempts_by_id.get(r.original_attempt_id) if r.original_attempt_id else None
        if attempt is None:
            attempt = fallback_by_problem.get(r.problem_id)
        problem = _load_problem(attempt) if attempt else None
        if not problem:
            continue  # skip unresolvable
        items.append({
            "review_id": r.id,
            "problem_id": r.problem_id,
            "times_reviewed": r.times_reviewed,
            "interval_days": r.interval_days,
            "grade": attempt.grade,
            "unit": attempt.unit,
            "lesson": attempt.lesson,
            "original_stage": attempt.stage,
            "problem": problem,
        })

    return {"items": items, "count": len(items)}


class ReviewSubmitIn(BaseModel):
    review_id: int
    user_answer: str = Field(default="", max_length=200)


# @tag MATH @tag MY_PROBLEMS
@router.post("/api/math/my-problems/submit-answer")
def submit_review_answer(req: ReviewSubmitIn, db: Session = Depends(get_db)):
    """Submit answer for a review problem. Phase 1: 1 correct = mastered."""
    row = db.query(MathWrongReview).filter_by(id=req.review_id).first()
    if not row:
        return {"error": "Review item not found"}
    if row.is_mastered:
        return {"error": "Already mastered", "is_correct": True, "is_mastered": True}

    # Resolve correct answer
    attempt = db.query(MathAttempt).filter_by(id=row.original_attempt_id).first() if row.original_attempt_id else None
    if attempt is None:
        attempt = (
            db.query(MathAttempt)
            .filter_by(problem_id=row.problem_id)
            .order_by(MathAttempt.id.desc())
            .first()
        )
    problem = _load_problem(attempt) if attempt else None
    if not problem:
        return {"error": "Original problem not found"}

    # Unify answer field: accept both "answer" and "correct_answer"
    correct_raw = str(
        problem.get("answer") or problem.get("correct_answer") or ""
    ).strip()
    correct_letter = ""
    correct_answer = correct_raw
    # Resolve letter key → choice text when choices is list/dict
    choices = problem.get("choices")
    if correct_raw and len(correct_raw) == 1 and correct_raw.upper() in "ABCDEFGH":
        correct_letter = correct_raw.upper()
        if isinstance(choices, dict):
            correct_answer = str(choices.get(correct_letter, correct_raw)).strip()
        elif isinstance(choices, list):
            idx_c = ord(correct_letter) - 65
            if 0 <= idx_c < len(choices):
                c = str(choices[idx_c])
                correct_answer = c[2:].strip() if len(c) > 2 and c[1] in ".)" else c
    user_lower = req.user_answer.strip().lower()
    is_correct = (
        user_lower == correct_answer.lower()
        or (correct_letter and user_lower == correct_letter.lower())
    )

    row.times_reviewed += 1

    # Miss penalty: overdue reviews reset consecutive_correct streak
    today = datetime.now().date()
    days_overdue = 0
    if row.next_review_date:
        try:
            due = datetime.strptime(row.next_review_date, "%Y-%m-%d").date()
            days_overdue = max(0, (today - due).days)
        except (ValueError, TypeError):
            pass
    if days_overdue >= 2:
        row.consecutive_correct = 0
    elif days_overdue == 1:
        row.consecutive_correct = 0

    xp_earned = 0
    if is_correct:
        row.consecutive_correct = (row.consecutive_correct or 0) + 1
        streak_engine.mark_math_done(db)
        if row.consecutive_correct >= 2:
            row.is_mastered = True
            try:
                xp_earned = xp_engine.award_xp(db, "math_problem_mastered", detail=row.problem_id)
            except Exception as e:
                logger.warning("XP award failed: %s", e)
        else:
            # Apply miss penalty to interval scheduling
            base_days = row.interval_days or 1
            if days_overdue == 1:
                base_days = max(1, int(base_days * 0.7))
            elif days_overdue >= 2:
                base_days = _INTERVALS[0]
                row.interval_days = base_days
            row.next_review_date = (
                datetime.now() + timedelta(days=base_days)
            ).strftime("%Y-%m-%d")
    else:
        row.consecutive_correct = 0
        idx = _INTERVALS.index(row.interval_days) if row.interval_days in _INTERVALS else 0
        next_idx = min(idx + 1, len(_INTERVALS) - 1)
        row.interval_days = _INTERVALS[next_idx]
        # Miss penalty on wrong answer: overdue shrinks next interval
        effective_days = row.interval_days
        if days_overdue == 1:
            effective_days = max(1, int(effective_days * 0.7))
        elif days_overdue >= 2:
            effective_days = _INTERVALS[0]
            row.interval_days = effective_days
        row.next_review_date = (
            datetime.now() + timedelta(days=effective_days)
        ).strftime("%Y-%m-%d")

    db.commit()
    return {
        "is_correct": is_correct,
        "correct_answer": correct_answer,
        "is_mastered": row.is_mastered,
        "consecutive_correct": row.consecutive_correct or 0,
        "next_review_date": row.next_review_date if not row.is_mastered else None,
        "xp_earned": xp_earned,
        "feedback": (lambda fb: (
            fb.get("correct", "") if is_correct else fb.get("incorrect", fb.get("wrong", ""))
        ) if isinstance(fb, dict) else str(fb or ""))(
            problem.get("feedback") or (
                problem.get("feedback_correct" if is_correct else "feedback_wrong") or ""
            )
        ),
    }
