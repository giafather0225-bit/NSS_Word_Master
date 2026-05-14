"""
from __future__ import annotations
routers/math_academy_spaced.py — Math Spaced Review endpoints
Section: Math
Dependencies: models.py (MathProgress, MathAttempt, MathWrongReview, MathSpacedReview),
              services/xp_engine.py, routers/math_academy.py (shared helpers)
API: GET  /api/math/spaced-review/count
     GET  /api/math/spaced-review/today
     POST /api/math/spaced-review/submit
"""

import logging
import random
import re
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

try:
    from ..database import get_db
    from ..models import MathWrongReview, MathSpacedReview
    from ..services import xp_engine
    from .math_academy import (
        _load_lesson_json,
        _stage_problems,
        _normalize_item,
        _grade_answer,
        _spaced_schedule,
    )
except ImportError:
    from database import get_db
    from models import MathWrongReview, MathSpacedReview
    from services import xp_engine
    from routers.math_academy import (
        _load_lesson_json,
        _stage_problems,
        _normalize_item,
        _grade_answer,
        _spaced_schedule,
    )

router = APIRouter()
logger = logging.getLogger(__name__)


# ── Local helpers ─────────────────────────────────────────────

def _unit_number(unit_id: str) -> int:
    """Extract numeric unit index from a unit id string (e.g. 'U4_...' → 4)."""
    m = re.search(r"[Uu](\d+)", unit_id or "")
    return int(m.group(1)) if m else 0


def _lesson_name(lesson_id: str) -> str:
    """Extract just the lesson file name from a lesson_id.

    lesson_id is stored as 'grade/unit/lesson' (e.g. 'G3/U1_place_value/L1_multiply').
    _load_lesson_json expects only the lesson segment.
    """
    return lesson_id.rsplit("/", 1)[-1]


def _answer_display(problem: dict) -> str:
    """Return human-readable correct answer (resolves letter keys to choice text)."""
    correct_raw = str(problem.get("correct_answer", problem.get("answer", ""))).strip()
    choices = problem.get("choices", [])
    if correct_raw.upper() in "ABCDEFGH" and len(correct_raw) == 1 and choices:
        idx = ord(correct_raw.upper()) - 65
        if 0 <= idx < len(choices):
            text = choices[idx]
            return text.split(")", 1)[-1].strip() if ")" in text else text.strip()
    return correct_raw


def _weakness_score(sr: MathSpacedReview, wrong_counts: dict[str, int]) -> int:
    """Weakness score = (100 - exit_quiz_pct) + wrong_review_count × 10.

    wrong_counts: pre-fetched {lesson_id: count} to avoid N+1 queries.
    """
    eq_pct = int(round((sr.exit_quiz_score / 5) * 100)) if sr.exit_quiz_score else 50
    wc = wrong_counts.get(sr.lesson_id, 0)
    return max(0, 100 - eq_pct) + wc * 10


def _build_sr_problem(p: dict, lesson_id: str, unit_id: str, grade: str, title: str) -> dict:
    """Serialize a problem dict for spaced review response (includes answer for client feedback)."""
    p = _normalize_item(p)
    fb = p.get("feedback", {})
    explanation = fb.get("incorrect", fb.get("correct", ""))
    return {
        "lesson_id": lesson_id,
        "unit_id": unit_id,
        "grade": grade,
        "lesson_title": title,
        "problem_id": p.get("id", ""),
        "stem": p.get("stem", p.get("question", "")),
        "type": p.get("type", "short"),
        "choices": p.get("choices", []),
        "correct_answer": str(p.get("correct_answer", p.get("answer", ""))).strip(),
        "answer_display": _answer_display(p),
        "explanation": explanation,
    }


# ── Pydantic schemas ──────────────────────────────────────────

class SpacedReviewAnswerIn(BaseModel):
    """Single answer within a spaced review submission."""
    lesson_id: str = Field(..., max_length=80)
    unit_id: str = Field(..., max_length=80)
    grade: str = Field(..., max_length=10)
    problem_id: str = Field(..., max_length=80)
    user_answer: str = Field("", max_length=200)


class SpacedReviewSubmitIn(BaseModel):
    """Batch spaced review submission."""
    answers: list[SpacedReviewAnswerIn] = Field(..., max_length=50)


# ── Endpoints ─────────────────────────────────────────────────

# @tag MATH @tag REVIEW
@router.get("/api/math/spaced-review/count")
def get_spaced_review_count(db: Session = Depends(get_db)) -> dict:
    """Return count of math spaced review lessons due today (for badge display)."""
    today_str = date.today().isoformat()
    count = (
        db.query(func.count(MathSpacedReview.id))
        .filter(MathSpacedReview.next_review_date <= today_str)
        .scalar()
        or 0
    )
    return {"count": int(count)}


# @tag MATH @tag REVIEW
@router.get("/api/math/spaced-review/today")
def get_spaced_review_today(db: Session = Depends(get_db)) -> dict:
    """Return all math spaced review problems due today, ordered oldest-first.

    Problem composition per lesson:
      U01-U03: 5 problems from practice_r1 pool
      U04+:    3 from current lesson + 2 interleaved from weakest prior lesson
    Includes correct answers so the client can show immediate feedback.
    """
    today_str = date.today().isoformat()

    due_lessons = (
        db.query(MathSpacedReview)
        .filter(MathSpacedReview.next_review_date <= today_str)
        .order_by(MathSpacedReview.next_review_date.asc())
        .all()
    )

    all_problems: list[dict] = []

    # Pre-fetch all spaced review rows + wrong review counts once — avoids N+1 inside the loop.
    all_sr_rows = db.query(MathSpacedReview).all() if due_lessons else []
    all_wrong_pids_global = (
        db.query(MathWrongReview.problem_id)
        .filter(MathWrongReview.is_mastered.is_(False))
        .all()
        if due_lessons else []
    )

    for sr in due_lessons:
        data = _load_lesson_json(sr.grade, sr.unit_id, _lesson_name(sr.lesson_id))
        if not data:
            continue

        current_pool = _stage_problems(data, "practice_r1") or _stage_problems(data, "exit_quiz")
        unit_num = _unit_number(sr.unit_id)
        lesson_title = data.get("title", sr.lesson_id)

        lesson_problems: list[dict] = []

        if unit_num >= 4 and len(current_pool) >= 3:
            # 3 random from current lesson
            sampled = random.sample(current_pool, min(3, len(current_pool)))
            for p in sampled:
                lesson_problems.append(_build_sr_problem(p, sr.lesson_id, sr.unit_id, sr.grade, lesson_title))

            # 2 interleaved from weakest prior lesson (Python-side filter — no extra DB query)
            earlier = [
                p for p in all_sr_rows
                if p.id != sr.id
                and p.grade == sr.grade
                and _unit_number(p.unit_id) < unit_num
            ]
            if earlier:
                lesson_ids = {p.lesson_id for p in earlier}
                wrong_counts: dict[str, int] = {}
                for (pid,) in all_wrong_pids_global:
                    for lid in lesson_ids:
                        if lid in pid:
                            wrong_counts[lid] = wrong_counts.get(lid, 0) + 1
                weakest_sr = max(earlier, key=lambda p: _weakness_score(p, wrong_counts))
                w_data = _load_lesson_json(weakest_sr.grade, weakest_sr.unit_id, _lesson_name(weakest_sr.lesson_id))
                if w_data:
                    w_pool = _stage_problems(w_data, "practice_r1")
                    w_sampled = random.sample(w_pool, min(2, len(w_pool)))
                    for p in w_sampled:
                        lesson_problems.append(_build_sr_problem(
                            p, weakest_sr.lesson_id, weakest_sr.unit_id, weakest_sr.grade,
                            w_data.get("title", weakest_sr.lesson_id),
                        ))
        else:
            # U01-U03: 5 random from current lesson
            sampled = random.sample(current_pool, min(5, len(current_pool)))
            for p in sampled:
                lesson_problems.append(_build_sr_problem(p, sr.lesson_id, sr.unit_id, sr.grade, lesson_title))

        # Shuffle within each lesson's problem set for variety
        random.shuffle(lesson_problems)
        all_problems.extend(lesson_problems)

    return {
        "count": len(all_problems),
        "lesson_count": len(due_lessons),
        "problems": all_problems,
    }


# @tag MATH @tag REVIEW
@router.post("/api/math/spaced-review/submit")
def submit_spaced_review(req: SpacedReviewSubmitIn, db: Session = Depends(get_db)) -> dict:
    """Grade batch spaced review answers, reschedule each lesson, and award XP once.

    Miss penalty (applied to next interval):
      1 day overdue  → interval × 0.7
      2+ days overdue → reset to first interval in schedule
    """
    today = date.today()
    today_str = today.isoformat()
    now = datetime.now().isoformat()

    results: list[dict] = []
    lessons_seen: dict[str, tuple[str, str, str]] = {}  # key → (grade, unit_id, lesson_id)

    for ans in req.answers:
        data = _load_lesson_json(ans.grade, ans.unit_id, _lesson_name(ans.lesson_id))
        problem: dict | None = None
        if data:
            pool = _stage_problems(data, "practice_r1") or _stage_problems(data, "exit_quiz")
            problem = next((p for p in pool if p.get("id") == ans.problem_id), None)

        if problem:
            is_correct, correct_display = _grade_answer(problem, ans.user_answer)
        else:
            is_correct = False
            correct_display = ans.problem_id

        results.append({
            "problem_id": ans.problem_id,
            "lesson_id": ans.lesson_id,
            "is_correct": is_correct,
            "correct_answer": correct_display,
        })
        key = f"{ans.grade}|{ans.unit_id}|{ans.lesson_id}"
        lessons_seen[key] = (ans.grade, ans.unit_id, ans.lesson_id)

    # Compute per-lesson accuracy from graded results
    lesson_correct: dict[str, int] = {}
    lesson_total: dict[str, int] = {}
    for r in results:
        lid = r["lesson_id"]
        lesson_total[lid] = lesson_total.get(lid, 0) + 1
        if r["is_correct"]:
            lesson_correct[lid] = lesson_correct.get(lid, 0) + 1

    updated_lessons: list[dict] = []
    for key, (grade, unit_id, lesson_id) in lessons_seen.items():
        sr = (
            db.query(MathSpacedReview)
            .filter_by(grade=grade, unit_id=unit_id, lesson_id=lesson_id)
            .first()
        )
        if not sr:
            continue

        # Days overdue for miss penalty
        days_overdue = 0
        try:
            due_date = date.fromisoformat(sr.next_review_date)
            days_overdue = max(0, (today - due_date).days)
        except Exception:
            pass

        intervals = _spaced_schedule(
            int(round((sr.exit_quiz_score / 5) * 100)) if sr.exit_quiz_score else 50
        )

        # Review accuracy gates interval advancement:
        #   ≥80% correct → advance to next interval
        #   <80% correct → reset to first interval (re-study needed)
        l_total = lesson_total.get(lesson_id, 0)
        l_correct = lesson_correct.get(lesson_id, 0)
        review_pct = (l_correct / l_total * 100) if l_total else 0

        if review_pct >= 80:
            next_idx = min((sr.interval_index or 0) + 1, len(intervals) - 1)
        else:
            next_idx = 0

        base_interval = intervals[next_idx]

        if days_overdue == 1:
            adjusted = max(1, int(base_interval * 0.7))
        elif days_overdue >= 2:
            adjusted = intervals[0]
            next_idx = 0
        else:
            adjusted = base_interval

        sr.interval_days = adjusted
        sr.interval_index = next_idx
        sr.next_review_date = (today + timedelta(days=adjusted)).isoformat()
        sr.last_reviewed_at = now

        updated_lessons.append({
            "lesson_id": lesson_id,
            "next_review_date": sr.next_review_date,
            "interval_days": adjusted,
            "review_accuracy": round(review_pct, 1),
        })

    xp_earned = 0
    try:
        xp_earned = xp_engine.award_xp(db, "math_spaced_review")
    except Exception as e:
        logger.warning("Spaced review XP award failed: %s", e)

    db.commit()

    return {
        "status": "ok",
        "results": results,
        "lessons_updated": updated_lessons,
        "xp_earned": xp_earned,
    }
