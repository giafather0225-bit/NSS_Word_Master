"""
routers/math_spaced_review.py — Math spaced-review queue (count / today / submit).
Section: Math
Dependencies: models/math, _math_academy_common
API endpoints:
  GET  /api/math/spaced-review/count
  GET  /api/math/spaced-review/today
  POST /api/math/spaced-review/submit
"""
import logging
import random
from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends

from backend.database import get_db
from backend.routers._math_academy_common import (
    MathSpacedReview, MathWrongReview,
    _load_lesson_json, _stage_problems, _grade_answer,
    _spaced_schedule, _normalize_item,
    _unit_number, _lesson_name, _answer_display, _weakness_score, _build_sr_problem,
    SpacedReviewSubmitIn,
)

router = APIRouter()
logger = logging.getLogger(__name__)


# @tag MATH @tag REVIEW @tag SM2
@router.get("/api/math/spaced-review/count")
def get_spaced_review_count(db: Session = Depends(get_db)) -> dict:
    """Return number of spaced-review lessons due today."""
    today_str = date.today().isoformat()
    count = (
        db.query(func.count(MathSpacedReview.id))
        .filter(MathSpacedReview.next_review_date <= today_str)
        .scalar() or 0
    )
    return {"count": int(count)}


# @tag MATH @tag REVIEW @tag SM2
@router.get("/api/math/spaced-review/today")
def get_spaced_review_today(db: Session = Depends(get_db)) -> dict:
    """Return today's spaced-review problems with interleaving for U04+."""
    today_str = date.today().isoformat()
    due_lessons = (
        db.query(MathSpacedReview)
        .filter(MathSpacedReview.next_review_date <= today_str)
        .order_by(MathSpacedReview.next_review_date.asc())
        .all()
    )

    all_problems: list[dict] = []

    # Pre-fetch to avoid N+1 queries inside the loop
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
            # U04+: 3 current + 2 from weakest prior lesson (interleaving)
            sampled = random.sample(current_pool, min(3, len(current_pool)))
            for p in sampled:
                lesson_problems.append(
                    _build_sr_problem(p, sr.lesson_id, sr.unit_id, sr.grade, lesson_title)
                )

            earlier = [
                p for p in all_sr_rows
                if p.id != sr.id and p.grade == sr.grade and _unit_number(p.unit_id) < unit_num
            ]
            if earlier:
                lesson_ids = {p.lesson_id for p in earlier}
                wrong_counts: dict[str, int] = {}
                for (pid,) in all_wrong_pids_global:
                    for lid in lesson_ids:
                        if lid in pid:
                            wrong_counts[lid] = wrong_counts.get(lid, 0) + 1

                weakest_sr = max(earlier, key=lambda p: _weakness_score(p, wrong_counts))
                w_data = _load_lesson_json(
                    weakest_sr.grade, weakest_sr.unit_id, _lesson_name(weakest_sr.lesson_id)
                )
                if w_data:
                    w_pool = _stage_problems(w_data, "practice_r1")
                    w_sampled = random.sample(w_pool, min(2, len(w_pool)))
                    for p in w_sampled:
                        lesson_problems.append(
                            _build_sr_problem(
                                p, weakest_sr.lesson_id, weakest_sr.unit_id,
                                weakest_sr.grade, w_data.get("title", weakest_sr.lesson_id),
                            )
                        )
        else:
            # U01-U03: 5 problems from current lesson only
            sampled = random.sample(current_pool, min(5, len(current_pool)))
            for p in sampled:
                lesson_problems.append(
                    _build_sr_problem(p, sr.lesson_id, sr.unit_id, sr.grade, lesson_title)
                )

        random.shuffle(lesson_problems)
        all_problems.extend(lesson_problems)

    return {
        "count": len(all_problems),
        "lesson_count": len(due_lessons),
        "problems": all_problems,
    }


# @tag MATH @tag REVIEW @tag SM2 @tag XP
@router.post("/api/math/spaced-review/submit")
def submit_spaced_review(req: SpacedReviewSubmitIn, db: Session = Depends(get_db)) -> dict:
    """Grade spaced-review answers and advance SM-2 intervals per lesson."""
    today = date.today()
    today_str = today.isoformat()
    now = datetime.now().isoformat()

    results: list[dict] = []
    lessons_seen: dict[str, tuple[str, str, str]] = {}

    for ans in req.answers:
        data = _load_lesson_json(ans.grade, ans.unit_id, _lesson_name(ans.lesson_id))
        problem: Optional[dict] = None
        if data:
            pool = _stage_problems(data, "practice_r1") or _stage_problems(data, "exit_quiz")
            problem = next((p for p in pool if p.get("id") == ans.problem_id), None)

        if problem:
            is_correct, correct_display = _grade_answer(problem, ans.user_answer)
        else:
            is_correct = False
            correct_display = ans.problem_id

        results.append({
            "problem_id": ans.problem_id, "lesson_id": ans.lesson_id,
            "is_correct": is_correct, "correct_answer": correct_display,
        })
        key = f"{ans.grade}|{ans.unit_id}|{ans.lesson_id}"
        lessons_seen[key] = (ans.grade, ans.unit_id, ans.lesson_id)

    # Aggregate per-lesson accuracy
    lesson_correct: dict[str, int] = {}
    lesson_total: dict[str, int] = {}
    for r in results:
        lid = r["lesson_id"]
        lesson_total[lid] = lesson_total.get(lid, 0) + 1
        if r["is_correct"]:
            lesson_correct[lid] = lesson_correct.get(lid, 0) + 1

    updated_lessons: list[dict] = []
    for key, (grade, unit_id, lesson_id) in lessons_seen.items():
        sr = db.query(MathSpacedReview).filter_by(
            grade=grade, unit_id=unit_id, lesson_id=lesson_id
        ).first()
        if not sr:
            continue

        days_overdue = 0
        try:
            due_date = date.fromisoformat(sr.next_review_date)
            days_overdue = max(0, (today - due_date).days)
        except Exception:
            pass

        intervals = _spaced_schedule(
            int(round((sr.exit_quiz_score / 5) * 100)) if sr.exit_quiz_score else 50
        )
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

    db.commit()

    return {
        "status": "ok",
        "results": results,
        "lessons_updated": updated_lessons,
        "xp_earned": 0,
    }
