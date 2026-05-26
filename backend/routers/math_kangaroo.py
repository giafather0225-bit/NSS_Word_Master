"""
routers/math_kangaroo.py — Math Kangaroo Practice API
Section: Math
Dependencies: models (MathKangarooProgress, XPLog), services/streak_engine,
              math_kangaroo_helpers (load_set, past_paper_sections, etc.)

API:
  GET  /api/math/kangaroo/sets
  GET  /api/math/kangaroo/set/{set_id}
  POST /api/math/kangaroo/submit           (Entire set, weighted scoring)
"""


import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

try:
    from ..database import get_db
    from ..models import MathKangarooProgress
    from ..services import streak_engine
    from . import math_kangaroo_helpers as helpers
except ImportError:  # pragma: no cover — fallback for direct execution
    from database import get_db
    from models import MathKangarooProgress
    from services import streak_engine
    import math_kangaroo_helpers as helpers  # type: ignore

router = APIRouter()
logger = logging.getLogger(__name__)


# ── GET /sets ────────────────────────────────────────────────

# @tag MATH @tag KANGAROO
@router.get("/api/math/kangaroo/sets")
def kangaroo_sets(db: Session = Depends(get_db)) -> dict[str, Any]:
    """List available Kangaroo practice sets with progress metadata."""
    result: list[dict[str, Any]] = []
    if not helpers.KANGAROO_DIR.is_dir():
        return {"sets": []}
    # Batch-fetch all progress rows once — avoid N+1 (one query per set).
    progress_by_id = {
        p.set_id: p for p in db.query(MathKangarooProgress).all()
    }
    for path in sorted(helpers.KANGAROO_DIR.glob("*.json")):
        try:
            data = helpers.read_set_cached(str(path), path.stat().st_mtime)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            logger.warning("Skipping unreadable set %s: %s", path.name, exc)
            continue
        set_id = data.get("set_id") or path.stem
        prog = progress_by_id.get(set_id)
        entry = {
            "set_id": set_id,
            "title": data.get("title", set_id),
            "level": data.get("level", ""),
            "level_label": data.get("level_label", ""),
            "grade_range": data.get("grade_range", ""),
            "total_questions": int(data.get("total_questions", 0) or 0),
            "time_limit_minutes": int(data.get("time_limit_minutes", 0) or 0),
            "max_score": int(data.get("max_score", 0) or 0),
            "category": data.get("category", "full_test"),
            "drill_topic": data.get("drill_topic"),
            "source_year": data.get("source_year"),
            "source_contest": data.get("source_contest"),
            "source_country": data.get("source_country"),
            "competition": helpers.competition_label(set_id),
            "best_score": prog.score if prog else None,
            "completed": bool(prog and prog.completed_at),
        }
        if helpers.is_past_paper(data):
            pdf_file = data.get("pdf_file", "")
            entry["pdf_file"] = pdf_file
            entry["pdf_available"] = helpers.pdf_available(pdf_file)
            entry["answers_pending"] = bool(data.get("answers_pending"))
        result.append(entry)
    return {"sets": result}


# ── GET /set/{set_id} ────────────────────────────────────────

# @tag MATH @tag KANGAROO
@router.get("/api/math/kangaroo/set/{set_id}")
def kangaroo_set(set_id: str) -> dict[str, Any]:
    """Return full set structure with answers/solutions stripped from questions."""
    data = helpers.load_set(set_id)

    if helpers.is_past_paper(data):
        # Past paper: return PDF-exam metadata (no answers, no questions)
        sections_meta = helpers.past_paper_sections(data)
        numbering = data.get("numbering") or {}
        pdf_file = data.get("pdf_file", "")
        return {
            "set_id": data.get("set_id", set_id),
            "title": data.get("title", set_id),
            "level": data.get("level", ""),
            "level_label": data.get("level_label", ""),
            "grade_range": data.get("grade_range", ""),
            "total_questions": int(data.get("total_questions", 0) or 0),
            "time_limit_minutes": int(data.get("time_limit_minutes", 0) or 0),
            "max_score": int(data.get("max_score", 0) or 0),
            "category": data.get("category", "past_paper"),
            "source_type": data.get("source_type"),
            "source_year": data.get("source_year"),
            "source_contest": data.get("source_contest"),
            "source_country": data.get("source_country"),
            "disclaimer": data.get("disclaimer", ""),
            "pdf_file": pdf_file,
            "pdf_available": helpers.pdf_available(pdf_file),
            "answers_pending": bool(data.get("answers_pending")),
            "sections_meta": sections_meta,
            "numbering_style": numbering.get("style", "sequential"),
        }

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
                "image": q.get("image"),
                "image_only": bool(q.get("image_only", False)),
                "image_description": q.get("image_description"),
                "options": q.get("options", {}),
                "pdf_page": q.get("pdf_page"),
                "image_required": bool(q.get("image_required", False)),
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


# ── POST /submit ─────────────────────────────────────────────

class KangarooAnswerItem(BaseModel):
    question_id: Optional[str] = Field(None, max_length=40)
    question_number: Optional[int] = None
    answer: Optional[str] = Field(None, max_length=10)


class KangarooSubmitIn(BaseModel):
    set_id: str = Field(..., max_length=80)
    answers: Union[List[KangarooAnswerItem], Dict[str, str]] = []
    time_spent_seconds: Optional[int] = None


def _grade_past_paper(data, req, answer_map, db) -> dict[str, Any]:
    """Grade past-paper submission using flat answers dict + scoring config."""
    if data.get("answers_pending"):
        raise HTTPException(status_code=409, detail="Answer key pending for this set")
    correct_map: dict[str, str] = {
        str(k): str(v).strip().upper()
        for k, v in (data.get("answers") or {}).items()
    }

    # Build per-question detail lookup from flat questions array (new schema)
    q_detail: dict[str, dict[str, Any]] = {}
    for q in data.get("questions") or []:
        key = str(q.get("number", ""))
        if key:
            q_detail[key] = q

    section_stats: list[dict[str, Any]] = []
    details: list[dict[str, Any]] = []
    total_score = 0
    total_max = int(data.get("max_score", 0) or 0)
    total_correct = 0
    wrong_count = 0
    unanswered_count = 0
    total_q = int(data.get("total_questions", 0) or 0)

    for sec in helpers.past_paper_sections(data):
        pts = sec["points"]
        labels = sec["questions"]
        sec_correct = 0
        sec_score = 0
        for label in labels:
            given = answer_map.get(label, "")
            correct_ans = correct_map.get(label, "")
            is_correct = bool(correct_ans) and given == correct_ans
            if is_correct:
                sec_correct += 1
                sec_score += pts
                total_correct += 1
                total_score += pts
            elif given:
                wrong_count += 1
            else:
                unanswered_count += 1
            qd = q_detail.get(label, {})
            details.append({
                "question": label,
                "student": given or None,
                "correct": correct_ans,
                "is_correct": is_correct,
                "points": pts,
                "topic": qd.get("topic", ""),
                "pdf_page": qd.get("pdf_page"),
                "solution": qd.get("solution", ""),
                "solution_steps": qd.get("solution_steps") or [],
            })
        section_stats.append({
            "key": sec["key"],
            "name": sec["name"],
            "correct": sec_correct,
            "total": len(labels),
            "score": sec_score,
            "max": pts * len(labels),
        })

    percentage = round((total_score / total_max * 100), 1) if total_max else 0.0
    perfect = total_max > 0 and total_score == total_max

    # Persist best
    now_iso = datetime.now().isoformat()
    row = db.query(MathKangarooProgress).filter_by(set_id=req.set_id).first()
    is_new_best = False
    if not row:
        row = MathKangarooProgress(
            set_id=req.set_id,
            category=data.get("category", "past_paper"),
            difficulty_level=data.get("level", ""),
            level=data.get("level", ""),
            score=total_score,
            max_score=total_max,
            total=total_q,
            time_spent_seconds=req.time_spent_seconds,
            answers_json=json.dumps(answer_map),
            completed_at=now_iso,
        )
        db.add(row)
        is_new_best = True
    else:
        row.level = data.get("level", row.level or "")
        row.category = data.get("category", row.category or "past_paper")
        row.max_score = total_max
        row.total = total_q
        if total_score > (row.score or 0):
            row.score = total_score
            row.time_spent_seconds = req.time_spent_seconds
            row.answers_json = json.dumps(answer_map)
            is_new_best = True
        row.completed_at = now_iso

    awarded = 0
    try:
        awarded += helpers.award_kangaroo_xp(db, req.set_id, "math_kangaroo_complete", 5)
        if percentage >= 80:
            awarded += helpers.award_kangaroo_xp(db, req.set_id, "math_kangaroo_80", 5)
        if perfect:
            awarded += helpers.award_kangaroo_xp(db, req.set_id, "math_kangaroo_perfect", 10)
    except Exception as exc:
        logger.warning("Kangaroo XP award failed: %s", exc)

    db.commit()

    try:
        streak_engine.mark_math_done(db)
    except Exception as exc:
        logger.warning("Streak math mark failed: %s", exc)

    return {
        "score": total_score,
        "max_score": total_max,
        "percentage": percentage,
        "correct_count": total_correct,
        "wrong_count": wrong_count,
        "unanswered_count": unanswered_count,
        "total_questions": total_q,
        "time_spent_seconds": req.time_spent_seconds or 0,
        "time_spent_formatted": helpers.format_time(req.time_spent_seconds),
        "grade_label": helpers.grade_label(percentage),
        "section_breakdown": section_stats,
        "details": details,
        "xp_earned": awarded,
        "perfect": perfect,
        "is_new_best": is_new_best,
        "is_past_paper": True,
        "pdf_file": data.get("pdf_file", ""),
        "title": data.get("title", req.set_id),
    }


# @tag MATH @tag KANGAROO @tag XP
@router.post("/api/math/kangaroo/submit")
def kangaroo_submit(req: KangarooSubmitIn, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Grade entire Kangaroo set with weighted scoring. Save best + award XP."""
    data = helpers.load_set(req.set_id)

    # Build answer_map: accept dict OR list form
    answer_map: dict[str, str] = {}
    if isinstance(req.answers, dict):
        answer_map = {str(k): (v or "").strip().upper() for k, v in req.answers.items()}
    else:
        for a in (req.answers or []):
            key = a.question_id if a.question_id is not None else (
                str(a.question_number) if a.question_number is not None else None)
            if key is not None:
                answer_map[str(key)] = (a.answer or "").strip().upper()

    if helpers.is_past_paper(data):
        return _grade_past_paper(data, req, answer_map, db)

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
                "image": q.get("image"),
                "image_only": bool(q.get("image_only", False)),
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
        awarded += helpers.award_kangaroo_xp(db, req.set_id, "math_kangaroo_complete", 5)
        if percentage >= 80:
            awarded += helpers.award_kangaroo_xp(db, req.set_id, "math_kangaroo_80", 5)
        if perfect:
            awarded += helpers.award_kangaroo_xp(db, req.set_id, "math_kangaroo_perfect", 10)
    except Exception as exc:
        logger.warning("Kangaroo XP award failed: %s", exc)

    db.commit()

    try:
        streak_engine.mark_math_done(db)
    except Exception as exc:
        logger.warning("Streak math mark failed: %s", exc)

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
        "time_spent_formatted": helpers.format_time(req.time_spent_seconds),
        "grade_label": helpers.grade_label(percentage),
        "sections": section_stats,
        "topic_breakdown": topic_breakdown,
        "questions_review": review,
        "xp_earned": awarded,
        "perfect": perfect,
        "is_new_best": is_new_best,
    }
