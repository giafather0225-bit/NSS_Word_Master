"""
routers/ckla.py — CKLA grade-aware catalog and content endpoints (9 endpoints).
Section: Academy
Dependencies: models/ckla, models/us_academy, database
API endpoints:
  GET  /api/academy/ckla/grades
  GET  /api/academy/ckla/title
  GET  /api/academy/ckla/domains
  GET  /api/academy/ckla/domains/{domain_num}/lessons
  GET  /api/academy/ckla/lessons/{lesson_id}
  GET  /api/academy/ckla/words/{word_id}
  GET  /api/academy/ckla/spelling/{unit}
  GET  /api/academy/ckla/grammar/{unit}
  GET  /api/academy/ckla/morphology/{unit}

Progress / Q&A / Badges → ckla_progress.py
Domain Test             → ckla_domain_test.py
Grade Final Test        → ckla_grade_test.py
SM-2 review             → routers/review.py (GET /api/review/today?source=ckla)
"""
import json
import logging
import random

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from backend.database import get_db
from backend.models.ckla import (
    CKLADomain, CKLALesson, CKLAQuestion,
    CKLAWordLesson, CKLALessonProgress,
    CKLASpelling, CKLAGrammar, CKLAMorphology,
)
from backend.models.us_academy import USAcademyWord
from backend.models.system import AppConfig
from backend.routers._ckla_common import (
    _CFG_DOMAIN_ORDER_FIXED,
    _SUPPORTED_GRADES, _GRADE_TITLES,
    _grade_rank, _progress_dict, _word_dict,
)

router = APIRouter(prefix="/api/academy/ckla", tags=["ckla"])


# ── Grades & Title ─────────────────────────────────────────────────────────────

@router.get("/grades")
# @tag ACADEMY CKLA
def get_grades(db: Session = Depends(get_db)):
    """Available CKLA grades with lesson counts."""
    result = []
    for g in _SUPPORTED_GRADES:
        count = (
            db.query(CKLALesson)
            .join(CKLADomain, CKLALesson.domain_id == CKLADomain.id)
            .filter(CKLADomain.grade == g, CKLADomain.is_active == True, CKLALesson.is_active == True)
            .count()
        )
        result.append({"grade": g, "title": _GRADE_TITLES.get(g, f"Grade {g}"), "lesson_count": count})
    return result


@router.get("/title")
# @tag ACADEMY CKLA
def get_title(grade: int = Query(3, ge=3, le=8), db: Session = Depends(get_db)):
    """Return localized title string for the given grade."""
    if grade not in _SUPPORTED_GRADES:
        raise HTTPException(status_code=404, detail="Grade not available")
    return {"grade": grade, "title": _GRADE_TITLES.get(grade, f"Grade {grade}")}


# ── Domains ────────────────────────────────────────────────────────────────────

@router.get("/domains")
# @tag ACADEMY CKLA
def get_domains(grade: int = Query(3, ge=3, le=8), db: Session = Depends(get_db)):
    """Domain list for the given grade, with all_complete flag."""
    domains = (
        db.query(CKLADomain)
        .filter_by(is_active=True, grade=grade)
        .order_by(CKLADomain.domain_num)
        .all()
    )
    # Bulk-fetch all lesson IDs across all domains in a single query
    domain_ids = [d.id for d in domains]
    all_lesson_ids_by_domain: dict[int, list[int]] = {d.id: [] for d in domains}
    if domain_ids:
        lessons_bulk = (
            db.query(CKLALesson.id, CKLALesson.domain_id)
            .filter(CKLALesson.domain_id.in_(domain_ids), CKLALesson.is_active == True)
            .all()
        )
        for lid, did in lessons_bulk:
            all_lesson_ids_by_domain[did].append(lid)

    all_ids = [lid for ids in all_lesson_ids_by_domain.values() for lid in ids]
    completed_set = set()
    if all_ids:
        completed_set = {
            p.lesson_id for p in
            db.query(CKLALessonProgress.lesson_id)
            .filter(
                CKLALessonProgress.lesson_id.in_(all_ids),
                CKLALessonProgress.completed == True,
            )
            .all()
        }

    total_lessons = len(all_ids)
    completed_lessons = len(completed_set)
    completion_pct = round(completed_lessons / total_lessons * 100) if total_lessons else 0

    order_cfg = db.query(AppConfig).filter_by(key=_CFG_DOMAIN_ORDER_FIXED).first()
    order_fixed = order_cfg and order_cfg.value == "true"

    test_mode_cfg = db.query(AppConfig).filter_by(key="test_mode").first()
    test_mode = test_mode_cfg and test_mode_cfg.value == "true"

    all_complete_by_num: dict[int, bool] = {}
    for d in domains:
        ids = all_lesson_ids_by_domain[d.id]
        all_complete_by_num[d.domain_num] = (
            len(ids) > 0 and all(lid in completed_set for lid in ids)
        )

    # Bulk-fetch domain test histories from AppConfig in one query
    history_keys = [f"ckla_domain_test_history_d{d.domain_num}_g{grade}" for d in domains]
    history_rows = (
        db.query(AppConfig)
        .filter(AppConfig.key.in_(history_keys))
        .all()
    ) if domain_ids else []
    history_map: dict[int, list] = {}
    for row in history_rows:
        # key format: ckla_domain_test_history_d{n}_g{grade}
        try:
            parts = row.key.split("_d")[1].split("_g")
            dnum = int(parts[0])
            history_map[dnum] = json.loads(row.value or "[]")
        except (IndexError, ValueError, json.JSONDecodeError):
            pass

    domain_list = []
    for d in domains:
        ids = all_lesson_ids_by_domain[d.id]
        is_all_complete = all_complete_by_num[d.domain_num]

        prev_num = d.domain_num - 1
        locked = (
            not test_mode
            and order_fixed
            and prev_num in all_complete_by_num
            and not all_complete_by_num[prev_num]
        )

        test_history = history_map.get(d.domain_num, [])
        best_entry = max(test_history, key=lambda e: e.get("score_pct", 0)) if test_history else None

        domain_list.append({
            "id":              d.id,
            "domain_num":      d.domain_num,
            "title":           d.title,
            "lesson_count":    d.lesson_count,
            "grade":           d.grade,
            "completed_count": sum(1 for lid in ids if lid in completed_set),
            "all_complete":    is_all_complete,
            "locked":          locked,
            "test_history":    test_history[:3],   # last 3 attempts for UI
            "best_score_pct":  best_entry.get("score_pct") if best_entry else None,
        })

    return {
        "rank":              _grade_rank(completion_pct),
        "completion_pct":    completion_pct,
        "total_lessons":     total_lessons,
        "completed_lessons": completed_lessons,
        "domains":           domain_list,
    }


@router.get("/domains/{domain_num}/lessons")
# @tag ACADEMY CKLA
def get_lessons(domain_num: int, grade: int = Query(3, ge=3, le=8), db: Session = Depends(get_db)):
    """Lesson list for domain (passage excluded, progress included)."""
    domain = db.query(CKLADomain).filter_by(domain_num=domain_num, grade=grade, is_active=True).first()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")

    test_mode_cfg = db.query(AppConfig).filter_by(key="test_mode").first()
    test_mode = test_mode_cfg and test_mode_cfg.value == "true"

    order_cfg = db.query(AppConfig).filter_by(key=_CFG_DOMAIN_ORDER_FIXED).first()
    if not test_mode and order_cfg and order_cfg.value == "true" and domain_num > 1:
        prev_domain = db.query(CKLADomain).filter_by(
            domain_num=domain_num - 1, grade=grade, is_active=True
        ).first()
        if prev_domain:
            prev_ids = [
                r.id for r in
                db.query(CKLALesson.id).filter_by(domain_id=prev_domain.id, is_active=True).all()
            ]
            if prev_ids:
                prev_completed = db.query(CKLALessonProgress).filter(
                    CKLALessonProgress.lesson_id.in_(prev_ids),
                    CKLALessonProgress.completed == True,
                ).count()
                if prev_completed < len(prev_ids):
                    raise HTTPException(
                        status_code=403,
                        detail=f"Complete Domain {domain_num - 1} first.",
                    )

    lessons = (
        db.query(CKLALesson)
        .filter_by(domain_id=domain.id, is_active=True)
        .order_by(CKLALesson.lesson_num)
        .all()
    )
    lesson_ids = [l.id for l in lessons]
    prog_map = {
        p.lesson_id: p
        for p in db.query(CKLALessonProgress)
        .filter(CKLALessonProgress.lesson_id.in_(lesson_ids))
        .all()
    }

    all_complete = bool(lessons) and all(
        _progress_dict(prog_map.get(l.id))["completed"] for l in lessons
    )
    return {
        "domain": {
            "id": domain.id, "domain_num": domain_num,
            "title": domain.title, "grade": grade,
            "all_complete": all_complete,
        },
        "lessons": [
            {
                "id":             l.id,
                "lesson_num":     l.lesson_num,
                "title":          l.title,
                "passage_chars":  l.passage_chars,
                "word_work_word": l.word_work_word or "",
                "progress":       _progress_dict(prog_map.get(l.id)),
            }
            for l in lessons
        ],
    }


# ── Lesson Detail ──────────────────────────────────────────────────────────────

@router.get("/lessons/{lesson_id}")
# @tag ACADEMY CKLA
def get_lesson(lesson_id: int, db: Session = Depends(get_db)):
    """Lesson detail: passage + vocab + questions + progress."""
    lesson = db.query(CKLALesson).filter_by(id=lesson_id, is_active=True).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    domain = db.query(CKLADomain).filter_by(id=lesson.domain_id).first()

    word_ids = [
        wl.word_id
        for wl in db.query(CKLAWordLesson).filter_by(lesson_id=lesson_id).all()
    ]
    words = (
        db.query(USAcademyWord)
        .filter(USAcademyWord.id.in_(word_ids))
        .order_by(USAcademyWord.word)
        .all()
    ) if word_ids else []

    all_questions = (
        db.query(CKLAQuestion)
        .filter_by(lesson_id=lesson_id)
        .order_by(CKLAQuestion.question_num)
        .all()
    )
    prog = db.query(CKLALessonProgress).filter_by(lesson_id=lesson_id).first()

    # Sample Q&A: Literal×2 + Inferential×2 + Evaluative×1 (spec §CKLA Q&A)
    by_kind: dict[str, list] = {"Literal": [], "Inferential": [], "Evaluative": []}
    for q in all_questions:
        bucket = by_kind.get(q.kind)
        if bucket is not None:
            bucket.append(q)
    sampled = (
        random.sample(by_kind["Literal"],     min(2, len(by_kind["Literal"])))
        + random.sample(by_kind["Inferential"], min(2, len(by_kind["Inferential"])))
        + random.sample(by_kind["Evaluative"],  min(1, len(by_kind["Evaluative"])))
    )
    remaining = [q for q in all_questions if q not in sampled]
    random.shuffle(remaining)
    while len(sampled) < 5 and remaining:
        sampled.append(remaining.pop())
    random.shuffle(sampled)

    return {
        "id":             lesson.id,
        "domain_num":     lesson.domain_num,
        "domain_title":   domain.title if domain else "",
        "lesson_num":     lesson.lesson_num,
        "title":          lesson.title,
        "passage":        lesson.passage,
        "passage_chars":  lesson.passage_chars,
        "word_work_word": lesson.word_work_word or "",
        "grade":          lesson.grade,
        "vocab": [_word_dict(w) for w in words],
        "questions": [
            {
                "id":           q.id,
                "num":          q.question_num,
                "kind":         q.kind,
                "question":     q.question_text,
                "model_answer": q.model_answer or "",
            }
            for q in sampled
        ],
        "progress": _progress_dict(prog),
    }


# ── Word Detail ────────────────────────────────────────────────────────────────

@router.get("/words/{word_id}")
# @tag ACADEMY CKLA
def get_word(word_id: int, db: Session = Depends(get_db)):
    """CKLA word detail."""
    word = db.query(USAcademyWord).filter_by(id=word_id, is_active=True).first()
    if not word:
        raise HTTPException(status_code=404, detail="Word not found")
    return _word_dict(word)


# ── Spelling / Grammar / Morphology ───────────────────────────────────────────

@router.get("/spelling/{unit}")
def get_spelling(unit: int, db: Session = Depends(get_db)):
    """Return all spelling weeks for a unit."""
    rows = (
        db.query(CKLASpelling)
        .filter(CKLASpelling.unit == unit)
        .order_by(CKLASpelling.week)
        .all()
    )
    weeks = []
    for row in rows:
        try:
            words = json.loads(row.words)
        except (ValueError, TypeError):
            words = []
        try:
            challenges = json.loads(row.challenge_words)
        except (ValueError, TypeError):
            challenges = []
        weeks.append({
            "week":            row.week,
            "pattern":         row.pattern or "",
            "words":           words,
            "challenge_words": challenges,
        })
    return {"unit": unit, "weeks": weeks}


@router.get("/grammar/{unit}")
def get_grammar(unit: int, db: Session = Depends(get_db)):
    """Return grammar topics for a unit."""
    row = db.query(CKLAGrammar).filter(CKLAGrammar.unit == unit).first()
    if not row:
        return {"unit": unit, "topics": []}
    try:
        topics = json.loads(row.topics)
    except (ValueError, TypeError):
        topics = []
    return {"unit": unit, "topics": topics}


@router.get("/morphology/{unit}")
def get_morphology(unit: int, db: Session = Depends(get_db)):
    """Return morphology topics for a unit."""
    row = db.query(CKLAMorphology).filter(CKLAMorphology.unit == unit).first()
    if not row:
        return {"unit": unit, "topics": []}
    try:
        topics = json.loads(row.topics)
    except (ValueError, TypeError):
        topics = []
    return {"unit": unit, "topics": topics}
