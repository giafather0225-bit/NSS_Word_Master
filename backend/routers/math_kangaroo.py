"""
routers/math_kangaroo.py — Math Kangaroo Practice API
Section: Math
Dependencies: models (MathKangarooProgress, XPLog), services/streak_engine

API:
  GET  /api/math/kangaroo/sets
  GET  /api/math/kangaroo/set/{set_id}
  POST /api/math/kangaroo/submit-answer    (Practice mode — single question)
  POST /api/math/kangaroo/submit           (Test mode — entire set, weighted)
"""

from __future__ import annotations

import json
import logging
from datetime import date, datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

try:
    from ..database import get_db
    from ..models import MathKangarooProgress, XPLog
    from ..services import streak_engine
except ImportError:  # pragma: no cover — fallback for direct execution
    from database import get_db
    from models import MathKangarooProgress, XPLog
    from services import streak_engine

router = APIRouter()
logger = logging.getLogger(__name__)

_KANGAROO_DIR = Path(__file__).parent.parent / "data" / "math" / "kangaroo"


# ── Helpers ─────────────────────────────────────────────────

# @tag MATH @tag KANGAROO
def _load_set(set_id: str) -> dict[str, Any]:
    """Load a Kangaroo set JSON by id or raise 404."""
    path = _KANGAROO_DIR / f"{set_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Set {set_id} not found")
    try:
        return json.loads(path.read_text("utf-8"))
    except json.JSONDecodeError as exc:
        logger.exception("Invalid JSON in %s", path)
        raise HTTPException(status_code=500, detail="Corrupt set data") from exc


# @tag MATH @tag KANGAROO
def _iter_questions(data: dict[str, Any]):
    """Yield (section_name, points_per_q, question) tuples for a loaded set."""
    for section in data.get("sections", []) or []:
        pts = int(section.get("points_per_question", 0) or 0)
        name = section.get("name", "")
        for q in section.get("questions", []) or []:
            yield name, pts, q


# @tag MATH @tag KANGAROO
def _grade_label(percentage: float) -> str:
    """Return an encouraging label for a score percentage."""
    if percentage >= 90:
        return "Outstanding!"
    if percentage >= 80:
        return "Excellent!"
    if percentage >= 70:
        return "Great job!"
    if percentage >= 60:
        return "Good effort!"
    return "Keep practicing!"


# @tag MATH @tag KANGAROO
def _format_time(seconds: int | None) -> str:
    """Format seconds as mm:ss."""
    s = max(0, int(seconds or 0))
    return f"{s // 60:02d}:{s % 60:02d}"


# @tag MATH @tag KANGAROO @tag XP
def _award_kangaroo_xp(db: Session, set_id: str, amount: int, label: str) -> int:
    """Insert an XPLog row directly (bypasses daily action dedup so each set counts)."""
    if amount <= 0:
        return 0
    today = date.today().isoformat()
    detail = f"kangaroo:{set_id}:{label}"
    existing = db.query(XPLog).filter(
        XPLog.action == "math_kangaroo_complete",
        XPLog.detail == detail,
        XPLog.earned_date == today,
    ).first()
    if existing:
        return 0
    db.add(XPLog(
        action="math_kangaroo_complete",
        xp_amount=amount,
        detail=detail,
        earned_date=today,
        created_at=datetime.now().isoformat(),
    ))
    return amount


# ── GET /sets ────────────────────────────────────────────────

# @tag MATH @tag KANGAROO
@router.get("/api/math/kangaroo/sets")
def kangaroo_sets(db: Session = Depends(get_db)) -> dict[str, Any]:
    """List available Kangaroo practice sets with progress metadata."""
    result: list[dict[str, Any]] = []
    if not _KANGAROO_DIR.is_dir():
        return {"sets": []}
    for path in sorted(_KANGAROO_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text("utf-8"))
        except Exception:
            logger.warning("Skipping unreadable set %s", path.name)
            continue
        set_id = data.get("set_id") or path.stem
        prog = db.query(MathKangarooProgress).filter_by(set_id=set_id).first()
        result.append({
            "set_id": set_id,
            "title": data.get("title", set_id),
            "level": data.get("level", ""),
            "level_label": data.get("level_label", ""),
            "grade_range": data.get("grade_range", ""),
            "total_questions": int(data.get("total_questions", 0) or 0),
            "time_limit_minutes": int(data.get("time_limit_minutes", 0) or 0),
            "max_score": int(data.get("max_score", 0) or 0),
            "category": data.get("category", "full_test"),
            "best_score": prog.score if prog else None,
            "completed": bool(prog and prog.completed_at),
        })
    return {"sets": result}


# ── GET /set/{set_id} ────────────────────────────────────────

# @tag MATH @tag KANGAROO
@router.get("/api/math/kangaroo/set/{set_id}")
def kangaroo_set(set_id: str) -> dict[str, Any]:
    """Return full set structure with answers/solutions stripped from questions."""
    data = _load_set(set_id)
    sections_out: list[dict[str, Any]] = []
    for section in data.get("sections", []) or []:
        qs_out: list[dict[str, Any]] = []
        for q in section.get("questions", []) or []:
            qs_out.append({
                "id": q.get("id"),
                "number": q.get("number"),
                "points": q.get("points"),
                "topic": q.get("topic", ""),
                "question_text": q.get("question_text", ""),
                "image_svg": q.get("image_svg"),
                "image_description": q.get("image_description"),
                "options": q.get("options", {}),
            })
        sections_out.append({
            "name": section.get("name", ""),
            "points_per_question": section.get("points_per_question", 0),
            "questions": qs_out,
        })
    return {
        "set_id": data.get("set_id", set_id),
        "title": data.get("title", set_id),
        "level": data.get("level", ""),
        "level_label": data.get("level_label", ""),
        "grade_range": data.get("grade_range", ""),
        "total_questions": data.get("total_questions", 0),
        "time_limit_minutes": data.get("time_limit_minutes", 0),
        "max_score": data.get("max_score", 0),
        "category": data.get("category", "full_test"),
        "disclaimer": data.get("disclaimer", ""),
        "sections": sections_out,
    }


# ── POST /submit-answer (Practice mode) ──────────────────────

class KangarooAnswerIn(BaseModel):
    set_id: str
    question_id: str
    answer: str


# @tag MATH @tag KANGAROO
@router.post("/api/math/kangaroo/submit-answer")
def kangaroo_submit_answer(req: KangarooAnswerIn) -> dict[str, Any]:
    """Grade a single question (Practice mode). Returns correctness + solution."""
    data = _load_set(req.set_id)
    target: dict[str, Any] | None = None
    target_points = 0
    for _, pts, q in _iter_questions(data):
        if str(q.get("id")) == req.question_id:
            target = q
            target_points = pts
            break
    if not target:
        raise HTTPException(status_code=404, detail="Question not found in set")
    correct = str(target.get("answer", "")).strip().upper()
    given = str(req.answer or "").strip().upper()
    is_correct = bool(correct) and given == correct
    return {
        "is_correct": is_correct,
        "correct_answer": correct,
        "solution": target.get("solution", ""),
        "points_earned": target_points if is_correct else 0,
    }


# ── POST /submit (Test mode) ─────────────────────────────────

class KangarooAnswerItem(BaseModel):
    question_id: str
    answer: str | None = None


class KangarooSubmitIn(BaseModel):
    set_id: str
    answers: list[KangarooAnswerItem] = []
    time_spent_seconds: int | None = None


# @tag MATH @tag KANGAROO @tag XP
@router.post("/api/math/kangaroo/submit")
def kangaroo_submit(req: KangarooSubmitIn, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Grade entire Kangaroo set with weighted scoring. Save best + award XP."""
    data = _load_set(req.set_id)
    answer_map: dict[str, str] = {
        a.question_id: (a.answer or "").strip().upper() for a in (req.answers or [])
    }

    section_stats: list[dict[str, Any]] = []
    topic_stats: dict[str, dict[str, int]] = {}
    review: list[dict[str, Any]] = []
    total_score = 0
    total_max = 0
    total_correct = 0
    total_questions = 0

    for section in data.get("sections", []) or []:
        name = section.get("name", "")
        pts = int(section.get("points_per_question", 0) or 0)
        correct_here = 0
        earned_here = 0
        qlist = section.get("questions", []) or []
        for q in qlist:
            qid = str(q.get("id"))
            correct_ans = str(q.get("answer", "")).strip().upper()
            given = answer_map.get(qid, "")
            is_correct = bool(correct_ans) and given == correct_ans
            if is_correct:
                correct_here += 1
                earned_here += pts
                total_correct += 1
                total_score += pts
            total_max += pts
            total_questions += 1

            topic = q.get("topic", "") or "other"
            bucket = topic_stats.setdefault(topic, {"correct": 0, "total": 0})
            bucket["total"] += 1
            if is_correct:
                bucket["correct"] += 1

            review.append({
                "id": qid,
                "number": q.get("number"),
                "points": pts,
                "topic": topic,
                "question_text": q.get("question_text", ""),
                "image_svg": q.get("image_svg"),
                "image_description": q.get("image_description"),
                "options": q.get("options", {}),
                "student_answer": given or None,
                "correct_answer": correct_ans,
                "is_correct": is_correct,
                "solution": q.get("solution", ""),
            })
        section_stats.append({
            "name": name,
            "correct": correct_here,
            "total": len(qlist),
            "points_earned": earned_here,
            "max_points": pts * len(qlist),
        })

    percentage = round((total_score / total_max * 100), 1) if total_max else 0.0
    perfect = total_max > 0 and total_score == total_max

    # ── Persist progress (keep best) ─────────────────────────
    now_iso = datetime.now().isoformat()
    row = db.query(MathKangarooProgress).filter_by(set_id=req.set_id).first()
    is_new_best = False
    if not row:
        row = MathKangarooProgress(
            set_id=req.set_id,
            category=data.get("category", "full_test"),
            difficulty_level=data.get("level", ""),
            level=data.get("level", ""),
            score=total_score,
            max_score=total_max,
            total=total_questions,
            time_spent_seconds=req.time_spent_seconds,
            answers_json=json.dumps(answer_map),
            completed_at=now_iso,
        )
        db.add(row)
        is_new_best = True
    else:
        row.level = data.get("level", row.level or "")
        row.category = data.get("category", row.category or "full_test")
        row.max_score = total_max
        row.total = total_questions
        if total_score > (row.score or 0):
            row.score = total_score
            row.time_spent_seconds = req.time_spent_seconds
            row.answers_json = json.dumps(answer_map)
            is_new_best = True
        row.completed_at = now_iso

    # ── XP awards ────────────────────────────────────────────
    awarded = 0
    try:
        awarded += _award_kangaroo_xp(db, req.set_id, 5, "complete")
        if percentage >= 80:
            awarded += _award_kangaroo_xp(db, req.set_id, 5, "score80")
        if perfect:
            awarded += _award_kangaroo_xp(db, req.set_id, 10, "perfect")
    except Exception as exc:
        logger.warning("Kangaroo XP award failed: %s", exc)

    try:
        streak_engine.mark_math_done(db)
    except Exception as exc:
        logger.warning("Streak math mark failed: %s", exc)

    db.commit()

    topic_breakdown = [
        {
            "topic": topic,
            "correct": v["correct"],
            "total": v["total"],
            "rate": round((v["correct"] / v["total"] * 100), 1) if v["total"] else 0.0,
        }
        for topic, v in sorted(topic_stats.items())
    ]

    return {
        "score": total_score,
        "max_score": total_max,
        "percentage": percentage,
        "correct": total_correct,
        "total_questions": total_questions,
        "time_spent_seconds": req.time_spent_seconds or 0,
        "time_spent_formatted": _format_time(req.time_spent_seconds),
        "grade_label": _grade_label(percentage),
        "sections": section_stats,
        "topic_breakdown": topic_breakdown,
        "questions_review": review,
        "xp_earned": awarded,
        "perfect": perfect,
        "is_new_best": is_new_best,
    }
