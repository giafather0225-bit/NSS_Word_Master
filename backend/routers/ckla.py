"""
routers/ckla.py — CKLA grade-aware reading curriculum API
Section: Academy
Dependencies: models/ckla, models/us_academy, database, services/ckla_grader
API:
  GET  /api/academy/ckla/grades                       — available grades
  GET  /api/academy/ckla/title                        — localized grade title
  GET  /api/academy/ckla/domains                      — domain list (grade-aware)
  GET  /api/academy/ckla/domains/{domain_num}/lessons — lesson list
  GET  /api/academy/ckla/lessons/{lesson_id}          — lesson detail
  GET  /api/academy/ckla/lessons/{lesson_id}/progress — progress query
  POST /api/academy/ckla/lessons/{lesson_id}/progress — progress update
  POST /api/academy/ckla/lessons/{lesson_id}/difficulty — rate difficulty
  POST /api/academy/ckla/questions/{question_id}/answer — AI graded answer
  GET  /api/academy/ckla/words/{word_id}              — word detail
  GET  /api/academy/ckla/badges                       — badge gallery
  POST /api/academy/ckla/badges/check                 — check + award new badges
  GET  /api/academy/ckla/domain-test/{domain_num}     — domain test questions
  POST /api/academy/ckla/domain-test/{domain_num}/submit — submit domain test
  GET  /api/academy/ckla/grade-final-test             — grade final test questions
  POST /api/academy/ckla/grade-final-test/submit      — submit grade final test

  GET  /api/academy/ckla/spelling/{unit}              — spelling weeks for a unit
  GET  /api/academy/ckla/grammar/{unit}               — grammar topics for a unit
  GET  /api/academy/ckla/morphology/{unit}            — morphology topics for a unit

SM-2 review: routers/ckla_review.py
"""

import json
import logging
import random
from datetime import date as _date, datetime, timedelta
from difflib import SequenceMatcher

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from backend.database import get_db
from backend.models.ckla import (
    CKLADomain, CKLALesson, CKLAQuestion,
    CKLAWordLesson, CKLALessonProgress, CKLAQuestionResponse,
    CKLABadge, CKLAUserBadge,
    CKLASpelling, CKLAGrammar, CKLAMorphology,
)
from backend.models.us_academy import USAcademyWord, USAcademyWordProgress
from backend.models.system import AppConfig
from backend.services.ckla_grader import grade_answer
from backend.services.xp_engine import award_xp
from backend.services.streak_engine import mark_ckla_done

router = APIRouter(prefix="/api/academy/ckla", tags=["ckla"])

NOW = lambda: datetime.now().isoformat(timespec="seconds")

# Grades currently supported (expand as content is added)
_SUPPORTED_GRADES = [3]
_GRADE_TITLES = {3: "Grade 3"}

_RANK_THRESHOLDS = [
    (100, "Master"),
    (76,  "Champion"),
    (51,  "Adventurer"),
    (26,  "Explorer"),
    (0,   "Beginner"),
]


def _grade_rank(completion_pct: float) -> str:
    for threshold, rank in _RANK_THRESHOLDS:
        if completion_pct >= threshold:
            return rank
    return "Beginner"


# ── Pydantic Schemas ──────────────────────────────────────────────────────────

class ProgressUpdate(BaseModel):
    reading_done:     bool | None = None
    vocab_done:       bool | None = None
    qa_done:          bool | None = None
    word_work_done:   bool | None = None
    word_work_answer: str | None = None   # student's free-typed answer for similarity check


class AnswerSubmit(BaseModel):
    user_answer: str


class DifficultyRating(BaseModel):
    rating: str = Field(..., pattern="^(easy|neutral|hard)$")


class DomainTestSubmit(BaseModel):
    answers: dict[int, str]   # {question_id: user_answer}
    time_taken_seconds: int | None = None


class GradeFinalTestSubmit(BaseModel):
    answers: dict[int, str]


# ── Helpers ───────────────────────────────────────────────────────────────────

# @tag ACADEMY CKLA
def _get_or_create_progress(db: Session, lesson_id: int) -> CKLALessonProgress:
    prog = db.query(CKLALessonProgress).filter_by(lesson_id=lesson_id).first()
    if not prog:
        lesson = db.query(CKLALesson).filter_by(id=lesson_id).first()
        prog = CKLALessonProgress(
            lesson_id=lesson_id,
            grade=lesson.grade if lesson else 3,
            started_at=NOW(),
        )
        db.add(prog)
        db.flush()
    return prog


# @tag ACADEMY CKLA
def _progress_dict(p: CKLALessonProgress | None) -> dict:
    if not p:
        return {
            "reading_done": False, "reading_done_at": None,
            "vocab_done": False, "qa_done": False, "word_work_done": False,
            "questions_attempted": 0, "questions_correct": 0,
            "completed": False, "completed_at": None, "last_active": None,
            "started_at": None, "difficulty_rating": None, "grade": 3,
        }
    return {
        "reading_done":        bool(p.reading_done),
        "reading_done_at":     p.reading_done_at,
        "vocab_done":          bool(p.vocab_done),
        "qa_done":             bool(p.qa_done),
        "word_work_done":      bool(p.word_work_done),
        "questions_attempted": p.questions_attempted or 0,
        "questions_correct":   p.questions_correct or 0,
        "completed":           bool(p.completed),
        "completed_at":        p.completed_at,
        "last_active":         p.last_active,
        "started_at":          p.started_at,
        "difficulty_rating":   p.difficulty_rating,
        "grade":               p.grade or 3,
    }


# @tag ACADEMY CKLA
def _word_dict(w: USAcademyWord) -> dict:
    return {
        "id":             w.id,
        "word":           w.word,
        "definition":     w.definition or "",
        "part_of_speech": w.part_of_speech or "",
        "audio_url":      w.audio_url or "",
        "example_1":      w.example_1 or "",
        "all_defs":       json.loads(w.synonyms_json or "[]"),
    }


# @tag ACADEMY CKLA
def _badge_dict(b: CKLABadge, earned_at: str | None = None) -> dict:
    return {
        "badge_key":       b.badge_key,
        "badge_name":      b.badge_name,
        "description":     b.description,
        "condition_type":  b.condition_type,
        "condition_value": b.condition_value,
        "image_path":      b.image_path,
        "earned":          earned_at is not None,
        "earned_at":       earned_at,
    }


# ── Routes ────────────────────────────────────────────────────────────────────

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
def get_title(grade: int = Query(3), db: Session = Depends(get_db)):
    """Return localized title string for the given grade."""
    if grade not in _SUPPORTED_GRADES:
        raise HTTPException(status_code=404, detail="Grade not available")
    return {"grade": grade, "title": _GRADE_TITLES.get(grade, f"Grade {grade}")}


@router.get("/domains")
# @tag ACADEMY CKLA
def get_domains(grade: int = Query(3), db: Session = Depends(get_db)):
    """Domain list for the given grade, with all_complete flag."""
    domains = (
        db.query(CKLADomain)
        .filter_by(is_active=True, grade=grade)
        .order_by(CKLADomain.domain_num)
        .all()
    )
    # Bulk-fetch completed lesson counts per domain (avoids N+1)
    all_lesson_ids_by_domain: dict[int, list[int]] = {}
    for d in domains:
        lessons = db.query(CKLALesson.id).filter_by(domain_id=d.id, is_active=True).all()
        all_lesson_ids_by_domain[d.id] = [l.id for l in lessons]

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

    # Read sequential-order config (default: free order)
    order_cfg = db.query(AppConfig).filter_by(key=f"ckla_domain_order_fixed").first()
    order_fixed = order_cfg and order_cfg.value == "true"

    # Build all_complete set keyed by domain_num for sequential-lock check
    all_complete_by_num: dict[int, bool] = {}
    for d in domains:
        ids = all_lesson_ids_by_domain[d.id]
        all_complete_by_num[d.domain_num] = (
            len(ids) > 0 and all(lid in completed_set for lid in ids)
        )

    domain_list = []
    for d in domains:
        ids = all_lesson_ids_by_domain[d.id]
        is_all_complete = all_complete_by_num[d.domain_num]

        # A domain is locked when sequential order is enforced AND
        # the previous domain (domain_num - 1) exists but is not yet all_complete.
        prev_num = d.domain_num - 1
        locked = (
            order_fixed
            and prev_num in all_complete_by_num
            and not all_complete_by_num[prev_num]
        )

        domain_list.append({
            "id":              d.id,
            "domain_num":      d.domain_num,
            "title":           d.title,
            "lesson_count":    d.lesson_count,
            "grade":           d.grade,
            "completed_count": sum(1 for lid in ids if lid in completed_set),
            "all_complete":    is_all_complete,
            "locked":          locked,
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
def get_lessons(domain_num: int, grade: int = Query(3), db: Session = Depends(get_db)):
    """Lesson list for domain (passage excluded, progress included)."""
    domain = db.query(CKLADomain).filter_by(domain_num=domain_num, grade=grade, is_active=True).first()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")

    # Enforce sequential domain order if configured
    order_cfg = db.query(AppConfig).filter_by(key="ckla_domain_order_fixed").first()
    if order_cfg and order_cfg.value == "true" and domain_num > 1:
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
    # Pad to 5 if any kind was short
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


@router.get("/lessons/{lesson_id}/progress")
# @tag ACADEMY CKLA
def get_lesson_progress(lesson_id: int, db: Session = Depends(get_db)):
    """Progress state for a lesson."""
    prog = db.query(CKLALessonProgress).filter_by(lesson_id=lesson_id).first()
    return _progress_dict(prog)


@router.post("/lessons/{lesson_id}/progress")
# @tag ACADEMY CKLA XP STREAK
def update_lesson_progress(
    lesson_id: int, req: ProgressUpdate, db: Session = Depends(get_db)
):
    """Record reading / vocab / Word Work completion.
    - All three done (first time) → XP ckla_lesson_complete + mark_ckla_done (streak)
    """
    lesson = db.query(CKLALesson).filter_by(id=lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    try:
        prog = _get_or_create_progress(db, lesson_id)
        now  = NOW()

        if req.reading_done is True and not prog.reading_done:
            prog.reading_done    = True
            prog.reading_done_at = now

        if req.vocab_done is True and not prog.vocab_done:
            prog.vocab_done = True
            # Register lesson words in SM-2 queue for tomorrow
            word_links = db.query(CKLAWordLesson).filter_by(lesson_id=lesson_id).all()
            word_ids   = [wl.word_id for wl in word_links]
            tomorrow   = (_date.today() + timedelta(days=1)).isoformat()
            today_str  = _date.today().isoformat()

            existing_ids = {
                p.word_id for p in
                db.query(USAcademyWordProgress)
                .filter(USAcademyWordProgress.word_id.in_(word_ids))
                .all()
            }
            word_map = {
                w.id: w for w in
                db.query(USAcademyWord).filter(USAcademyWord.id.in_(word_ids)).all()
            }
            for wid in word_ids:
                if wid not in existing_ids and wid in word_map:
                    db.add(USAcademyWordProgress(
                        word_id=wid,
                        word=word_map[wid].word,
                        next_review=tomorrow,
                        last_studied=today_str,
                    ))

        if req.qa_done is True and not prog.qa_done:
            prog.qa_done = True

        if req.word_work_done is True and not prog.word_work_done:
            if req.word_work_answer and lesson.word_work_word:
                # Reject if student typed only the focus word (trivially short / just the word)
                typed_lower = req.word_work_answer.strip().lower()
                word_lower  = lesson.word_work_word.strip().lower()
                if typed_lower == word_lower:
                    raise HTTPException(
                        status_code=400,
                        detail="Write a full sentence using the word, not just the word itself.",
                    )
                # Reject if answer ≥80% similar to hint (definition or example) — spec §Word Work
                focus_word_rec = (
                    db.query(USAcademyWord)
                    .filter(USAcademyWord.word == lesson.word_work_word)
                    .first()
                )
                if focus_word_rec:
                    hint_parts = [
                        p.strip() for p in [
                            focus_word_rec.definition or "",
                            focus_word_rec.example_1  or "",
                        ] if p.strip()
                    ]
                    for hint in hint_parts:
                        ratio = SequenceMatcher(None, typed_lower, hint.lower()).ratio()
                        if ratio >= 0.8:
                            raise HTTPException(
                                status_code=400,
                                detail="Your sentence is too close to the hint. Try using your own words!",
                            )
            prog.word_work_done = True

        prog.last_active = now

        # Lesson complete: all four tabs done for the first time
        if (prog.reading_done and prog.vocab_done and prog.qa_done and prog.word_work_done
                and not prog.completed):
            prog.completed    = True
            prog.completed_at = now
            award_xp(db, "ckla_lesson_complete", detail=str(lesson_id))
            mark_ckla_done(db)

            # Check daily lesson goal
            today_str = _date.today().isoformat()
            daily_goal_cfg = db.query(AppConfig).filter_by(key="ckla_daily_goal").first()
            daily_goal = int(daily_goal_cfg.value) if daily_goal_cfg else 1
            today_done = (
                db.query(CKLALessonProgress)
                .filter(
                    CKLALessonProgress.completed == True,
                    CKLALessonProgress.completed_at.like(f"{today_str}%"),
                )
                .count()
            )
            if today_done >= daily_goal:
                # Guard: only award once per day — check XPLog before awarding
                from backend.models.gamification import XPLog
                already_awarded = db.query(XPLog).filter(
                    XPLog.action == "ckla_daily_goal",
                    XPLog.detail == today_str,
                ).first()
                if not already_awarded:
                    award_xp(db, "ckla_daily_goal", detail=today_str)

        db.commit()
        return _progress_dict(prog)
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error("update_lesson_progress failed lesson_id=%s: %s", lesson_id, e)
        raise HTTPException(status_code=500, detail="Failed to update lesson progress")


@router.post("/lessons/{lesson_id}/difficulty")
# @tag ACADEMY CKLA
def rate_difficulty(
    lesson_id: int, req: DifficultyRating, db: Session = Depends(get_db)
):
    """Save student difficulty rating (easy / neutral / hard) for a lesson."""
    lesson = db.query(CKLALesson).filter_by(id=lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    try:
        prog = _get_or_create_progress(db, lesson_id)
        prog.difficulty_rating = req.rating
        db.commit()
        return {"lesson_id": lesson_id, "difficulty_rating": req.rating}
    except SQLAlchemyError as e:
        db.rollback()
        logger.error("rate_difficulty failed lesson_id=%s: %s", lesson_id, e)
        raise HTTPException(status_code=500, detail="Failed to save difficulty rating")


@router.post("/questions/{question_id}/answer")
# @tag ACADEMY CKLA AI
async def submit_answer(
    question_id: int, req: AnswerSubmit, db: Session = Depends(get_db)
):
    """Submit an answer → AI grading → save result. Max 2 attempts per question (1 retry)."""
    question = db.query(CKLAQuestion).filter_by(id=question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    # Enforce 1-retry limit: count prior responses for this question in the current progress
    prog_check = db.query(CKLALessonProgress).filter_by(lesson_id=question.lesson_id).first()
    if prog_check:
        prior = (
            db.query(CKLAQuestionResponse)
            .filter_by(question_id=question_id, lesson_progress_id=prog_check.id)
            .count()
        )
        if prior >= 2:
            raise HTTPException(
                status_code=400,
                detail="You have already used your retry for this question.",
            )

    lesson = db.query(CKLALesson).filter_by(id=question.lesson_id).first()
    passage = lesson.passage if lesson else ""

    try:
        result = await grade_answer(
            question_text=question.question_text,
            kind=question.kind,
            model_answer=question.model_answer or "",
            passage=passage,
            user_answer=req.user_answer,
        )
    except Exception as e:
        logger.error("CKLA grade_answer failed question_id=%s: %s", question_id, e)
        raise HTTPException(status_code=503, detail="Grading service unavailable")

    try:
        prog = _get_or_create_progress(db, question.lesson_id)

        response = CKLAQuestionResponse(
            question_id=question_id,
            lesson_progress_id=prog.id,
            user_answer=req.user_answer,
            ai_score=result.score,
            ai_feedback=result.feedback,
            needs_parent_review=result.needs_parent_review,
            created_at=NOW(),
        )
        db.add(response)

        prog.questions_attempted = (prog.questions_attempted or 0) + 1
        if result.score == 2:
            prog.questions_correct = (prog.questions_correct or 0) + 1
        prog.last_active = NOW()

        db.commit()
        db.refresh(response)
        return {
            "id":                  response.id,
            "ai_score":            response.ai_score,
            "ai_feedback":         response.ai_feedback or "",
            "needs_parent_review": bool(response.needs_parent_review),
            "provider":            result.provider,
        }
    except SQLAlchemyError as e:
        db.rollback()
        logger.error("submit_answer DB save failed question_id=%s: %s", question_id, e)
        raise HTTPException(status_code=500, detail="Failed to save answer")


@router.get("/words/{word_id}")
# @tag ACADEMY CKLA
def get_word(word_id: int, db: Session = Depends(get_db)):
    """CKLA word detail."""
    word = db.query(USAcademyWord).filter_by(id=word_id, is_active=True).first()
    if not word:
        raise HTTPException(status_code=404, detail="Word not found")
    return _word_dict(word)


# ── Badges ────────────────────────────────────────────────────────────────────

@router.get("/badges")
# @tag ACADEMY CKLA
def get_badges(grade: int = Query(3), db: Session = Depends(get_db)):
    """Badge gallery: all badges (earned flag included)."""
    badges = db.query(CKLABadge).order_by(CKLABadge.condition_value).all()
    earned_map = {
        ub.badge_key: ub.earned_at
        for ub in db.query(CKLAUserBadge).all()
    }
    return [_badge_dict(b, earned_map.get(b.badge_key)) for b in badges]


@router.post("/badges/check")
# @tag ACADEMY CKLA XP
def check_and_award_badges(grade: int = Query(3), db: Session = Depends(get_db)):
    """Check progress against badge conditions and award any newly earned badges.

    Returns list of newly awarded badge_keys (empty if none new).
    """
    newly_earned: list[dict] = []
    now = NOW()

    earned_keys = {ub.badge_key for ub in db.query(CKLAUserBadge).all()}
    badges = db.query(CKLABadge).all()

    # Pre-load all domains + lesson IDs + completed lesson IDs in bulk (avoid N+1)
    all_domains = db.query(CKLADomain).filter_by(is_active=True).all()
    domain_by_num_grade: dict[tuple, CKLADomain] = {(d.domain_num, d.grade): d for d in all_domains}

    all_lessons = db.query(CKLALesson.id, CKLALesson.domain_id).filter_by(is_active=True).all()
    domain_lesson_ids: dict[int, list[int]] = {}  # domain.id → [lesson_id]
    for lid, did in all_lessons:
        domain_lesson_ids.setdefault(did, []).append(lid)

    all_lesson_ids_flat = [lid for lid, _ in all_lessons]
    completed_ids: set[int] = set()
    if all_lesson_ids_flat:
        completed_ids = {
            p.lesson_id
            for p in db.query(CKLALessonProgress.lesson_id)
            .filter(
                CKLALessonProgress.lesson_id.in_(all_lesson_ids_flat),
                CKLALessonProgress.completed.is_(True),
            )
            .all()
        }

    for badge in badges:
        if badge.badge_key in earned_keys:
            continue

        earned = False
        if badge.condition_type == "domain_complete":
            domain_num = badge.condition_value
            domain = domain_by_num_grade.get((domain_num, grade))
            if domain:
                lesson_ids = domain_lesson_ids.get(domain.id, [])
                earned = bool(lesson_ids) and all(lid in completed_ids for lid in lesson_ids)

        elif badge.condition_type == "grade_complete":
            target_grade = badge.condition_value
            grade_domains = [d for d in all_domains if d.grade == target_grade]
            if grade_domains:
                grade_lesson_ids = [
                    lid for d in grade_domains
                    for lid in domain_lesson_ids.get(d.id, [])
                ]
                earned = bool(grade_lesson_ids) and all(lid in completed_ids for lid in grade_lesson_ids)

        if earned:
            db.add(CKLAUserBadge(badge_key=badge.badge_key, earned_at=now))
            newly_earned.append({"badge_key": badge.badge_key, "badge_name": badge.badge_name})

    if newly_earned:
        db.commit()

    return {"newly_earned": newly_earned}


# ── Domain Test ───────────────────────────────────────────────────────────────

@router.get("/domain-test/{domain_num}")
# @tag ACADEMY CKLA
def get_domain_test(
    domain_num: int, grade: int = Query(3), db: Session = Depends(get_db)
):
    """Return 10 domain test questions: 3 vocab_mc + 2 vocab_fill + 5 Q&A.

    ID scheme (no schema change needed):
      Q&A        → real question.id  (< 10000)
      vocab_mc   → word_id + 10000
      vocab_fill → word_id + 20000
    """
    domain = db.query(CKLADomain).filter_by(domain_num=domain_num, grade=grade, is_active=True).first()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")

    lessons = (
        db.query(CKLALesson)
        .filter_by(domain_id=domain.id, is_active=True)
        .all()
    )
    lesson_ids = [l.id for l in lessons]

    # ── Q&A questions (5) — one per lesson, shuffled ──────────────────────────
    # Bulk-fetch all questions for all lessons at once (avoids N+1)
    all_qs = (
        db.query(CKLAQuestion)
        .filter(CKLAQuestion.lesson_id.in_(lesson_ids))
        .all()
    ) if lesson_ids else []
    qs_by_lesson: dict[int, list] = {}
    for q in all_qs:
        qs_by_lesson.setdefault(q.lesson_id, []).append(q)

    qa_questions: list[dict] = []
    shuffled_lessons = lessons[:]
    random.shuffle(shuffled_lessons)
    for lesson in shuffled_lessons:
        qs = qs_by_lesson.get(lesson.id, [])
        if qs:
            q = random.choice(qs)
            qa_questions.append({
                "id":           q.id,
                "type":         "qa",
                "lesson_id":    lesson.id,
                "lesson_title": lesson.title,
                "kind":         q.kind,
                "question_text": q.question_text,
            })
        if len(qa_questions) >= 5:
            break

    # ── Vocab questions (5: 3 MC + 2 fill) ───────────────────────────────────
    # Get all words linked to this domain's lessons
    word_links = (
        db.query(CKLAWordLesson)
        .filter(CKLAWordLesson.lesson_id.in_(lesson_ids))
        .all()
    ) if lesson_ids else []

    word_ids = list({wl.word_id for wl in word_links})
    domain_words: list[USAcademyWord] = []
    if word_ids:
        domain_words = db.query(USAcademyWord).filter(USAcademyWord.id.in_(word_ids)).all()

    vocab_questions: list[dict] = []
    if len(domain_words) >= 5:
        chosen = random.sample(domain_words, 5)
        # All domain words used as distractor pool
        distractor_pool = [w for w in domain_words if w.word]

        for i, word in enumerate(chosen):
            q_type = "vocab_fill" if i >= 3 else "vocab_mc"
            base: dict = {
                "lesson_title": "",
                "question_text": word.definition or "",
                "word": word.word,
            }
            if q_type == "vocab_mc":
                # 3 distractors from other domain words
                others = [w for w in distractor_pool if w.id != word.id and w.word]
                distractors = [w.word for w in random.sample(others, min(3, len(others)))]
                choices = distractors + [word.word]
                random.shuffle(choices)
                base.update({
                    "id":             word.id + 10000,
                    "type":           "vocab_mc",
                    "choices":        choices,
                    "correct_answer": word.word,
                })
            else:
                base.update({
                    "id":   word.id + 20000,
                    "type": "vocab_fill",
                })
            vocab_questions.append(base)

    # ── Combine, shuffle, return ──────────────────────────────────────────────
    all_questions = qa_questions + vocab_questions
    random.shuffle(all_questions)

    return {
        "domain_num":   domain_num,
        "domain_title": domain.title,
        "grade":        grade,
        "questions":    all_questions,
    }


@router.post("/domain-test/{domain_num}/submit")
# @tag ACADEMY CKLA XP
async def submit_domain_test(
    domain_num: int,
    req: DomainTestSubmit,
    grade: int = Query(3),
    db: Session = Depends(get_db),
):
    """Grade domain test answers. Vocab (MC/fill) graded locally; Q&A via AI.

    ID ranges:
      < 10000  → Q&A (AI graded, score 0/1/2 → correct if score == 2)
      10000–19999 → vocab_mc  (correct_answer exact match)
      >= 20000    → vocab_fill (case-insensitive word match)
    """
    domain = db.query(CKLADomain).filter_by(domain_num=domain_num, grade=grade, is_active=True).first()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")

    total = len(req.answers)
    if total == 0:
        raise HTTPException(status_code=400, detail="No answers submitted")

    correct = 0
    results: list[dict] = []

    for qid_str, user_ans in req.answers.items():
        try:
            qid = int(qid_str)
        except ValueError:
            continue

        if qid >= 20000:
            # vocab_fill — fetch word by id offset, case-insensitive match
            word = db.query(USAcademyWord).filter_by(id=qid - 20000).first()
            is_correct = bool(
                word and user_ans.strip().lower() == (word.word or "").lower()
            )
            correct += int(is_correct)
            results.append({"question_id": qid, "score": 2 if is_correct else 0})

        elif qid >= 10000:
            # vocab_mc — the answer submitted should equal the correct word
            word = db.query(USAcademyWord).filter_by(id=qid - 10000).first()
            is_correct = bool(
                word and user_ans.strip().lower() == (word.word or "").lower()
            )
            correct += int(is_correct)
            results.append({"question_id": qid, "score": 2 if is_correct else 0})

        else:
            # Q&A — AI graded
            question = db.query(CKLAQuestion).filter_by(id=qid).first()
            if not question:
                continue
            lesson = db.query(CKLALesson).filter_by(id=question.lesson_id).first()
            passage = lesson.passage if lesson else ""
            try:
                result = await grade_answer(
                    question_text=question.question_text,
                    kind=question.kind,
                    model_answer=question.model_answer or "",
                    passage=passage,
                    user_answer=user_ans,
                )
                score = result.score
            except Exception:
                score = 0
            if score == 2:
                correct += 1
            results.append({"question_id": qid, "score": score})

    pct = round(correct / total * 100) if total else 0
    _dpct_cfg = db.query(AppConfig).filter_by(key="ckla_domain_pass_pct").first()
    _domain_pass_pct = int(_dpct_cfg.value) if _dpct_cfg and _dpct_cfg.value else 80
    passed = pct >= _domain_pass_pct

    xp_awarded = 0
    # Track consecutive failures for parent dashboard warning (spec: 3회 연속 실패)
    fail_key = f"ckla_domain_test_consec_fails_d{domain_num}_g{grade}"
    fail_cfg = db.query(AppConfig).filter_by(key=fail_key).first()
    if passed:
        xp_awarded = award_xp(db, "ckla_domain_test_pass", detail=f"domain_{domain_num}_grade_{grade}")
        if fail_cfg:
            fail_cfg.value = "0"
    else:
        new_count = int(fail_cfg.value) + 1 if fail_cfg else 1
        if fail_cfg:
            fail_cfg.value = str(new_count)
        else:
            db.add(AppConfig(key=fail_key, value=str(new_count)))

    # Save elapsed time (latest attempt wins)
    if req.time_taken_seconds is not None:
        time_key = f"ckla_domain_test_time_d{domain_num}_g{grade}"
        time_cfg = db.query(AppConfig).filter_by(key=time_key).first()
        if time_cfg:
            time_cfg.value = str(req.time_taken_seconds)
        else:
            db.add(AppConfig(key=time_key, value=str(req.time_taken_seconds)))

    # Save per-attempt score history (last 10, newest first)
    history_key = f"ckla_domain_test_history_d{domain_num}_g{grade}"
    history_cfg = db.query(AppConfig).filter_by(key=history_key).first()
    history: list = []
    if history_cfg and history_cfg.value:
        try:
            history = json.loads(history_cfg.value)
        except (json.JSONDecodeError, ValueError):
            history = []
    history.insert(0, {
        "score_pct": pct,
        "correct": correct,
        "total": total,
        "passed": passed,
        "date": datetime.now().date().isoformat(),
    })
    history = history[:10]
    if history_cfg:
        history_cfg.value = json.dumps(history)
    else:
        db.add(AppConfig(key=history_key, value=json.dumps(history)))

    db.commit()

    return {
        "domain_num":         domain_num,
        "grade":              grade,
        "total":              total,
        "correct":            correct,
        "score_pct":          pct,
        "passed":             passed,
        "xp_awarded":         xp_awarded,
        "results":            results,
        "time_taken_seconds": req.time_taken_seconds,
    }


# ── Grade Final Test ──────────────────────────────────────────────────────────

@router.get("/grade-final-test")
# @tag ACADEMY CKLA
def get_grade_final_test(grade: int = Query(3), db: Session = Depends(get_db)):
    """Return 27 grade final test questions: 15 vocab_mc + 10 Q&A + 2 word_work.

    ID scheme (no schema change):
      Q&A        < 10000 → real CKLAQuestion.id
      vocab_mc   = word_id + 10000
      word_work  = word_id + 30000
    """
    domains = (
        db.query(CKLADomain)
        .filter_by(grade=grade, is_active=True)
        .order_by(CKLADomain.domain_num)
        .all()
    )
    if not domains:
        return {"grade": grade, "questions": []}

    domain_ids = [d.id for d in domains]
    domain_map = {d.id: d for d in domains}

    # Gather all lesson_ids across all domains
    all_lessons = db.query(CKLALesson).filter(
        CKLALesson.domain_id.in_(domain_ids), CKLALesson.is_active == True
    ).all()
    lesson_map = {ls.id: ls for ls in all_lessons}
    lesson_ids = [ls.id for ls in all_lessons]

    # ── 10 Q&A: 1 per domain, balanced Literal/Inferential/Evaluative ──────────
    # Bulk-fetch all questions for all lessons at once (avoids N×M queries)
    all_questions_raw = (
        db.query(CKLAQuestion)
        .filter(CKLAQuestion.lesson_id.in_(lesson_ids))
        .all()
    ) if lesson_ids else []

    # Index by (lesson_id, kind) for O(1) lookup
    qs_by_lesson_kind: dict[tuple, list] = {}
    for q in all_questions_raw:
        key = (q.lesson_id, q.kind)
        qs_by_lesson_kind.setdefault(key, []).append(q)

    qa_questions: list[dict] = []
    kind_counts: dict[str, int] = {"Literal": 0, "Inferential": 0, "Evaluative": 0}
    for domain in domains:
        d_lessons = [ls for ls in all_lessons if ls.domain_id == domain.id]
        # Prefer Evaluative if under quota (2), then Inferential (4), else Literal (4)
        preferred: list[str] = []
        if kind_counts.get("Evaluative", 0) < 2:
            preferred = ["Evaluative", "Inferential", "Literal"]
        elif kind_counts.get("Inferential", 0) < 4:
            preferred = ["Inferential", "Literal", "Evaluative"]
        else:
            preferred = ["Literal", "Inferential", "Evaluative"]

        picked = None
        for kind in preferred:
            candidates = [
                q for ls in d_lessons
                for q in qs_by_lesson_kind.get((ls.id, kind), [])
            ]
            if candidates:
                picked_q = random.choice(candidates)
                picked_lesson = lesson_map.get(picked_q.lesson_id)
                picked = {
                    "id":           picked_q.id,
                    "type":         "qa",
                    "kind":         picked_q.kind,
                    "domain_num":   domain.domain_num,
                    "domain_title": domain.title,
                    "lesson_title": picked_lesson.title if picked_lesson else "",
                    "question_text": picked_q.question_text,
                }
                kind_counts[kind] = kind_counts.get(kind, 0) + 1
                break
        if picked:
            qa_questions.append(picked)
        if len(qa_questions) >= 10:
            break

    # ── Gather all vocab words for this grade ──────────────────────────────────
    word_links = db.query(CKLAWordLesson).filter(
        CKLAWordLesson.lesson_id.in_(lesson_ids)
    ).all()
    word_ids = list({wl.word_id for wl in word_links})
    all_words = db.query(USAcademyWord).filter(USAcademyWord.id.in_(word_ids)).all()
    random.shuffle(all_words)

    # ── 15 vocab_mc ────────────────────────────────────────────────────────────
    vocab_mc_words = all_words[:15] if len(all_words) >= 15 else all_words
    vocab_mc_questions: list[dict] = []
    for w in vocab_mc_words:
        distractors = random.sample(
            [x for x in all_words if x.id != w.id],
            min(3, len(all_words) - 1),
        )
        choices = [x.word for x in distractors] + [w.word]
        random.shuffle(choices)
        vocab_mc_questions.append({
            "id":           w.id + 10000,
            "type":         "vocab_mc",
            "domain_num":   None,
            "domain_title": "",
            "lesson_title": "",
            "question_text": w.definition or w.word,
            "word":         w.word,
            "choices":      choices,
        })

    # ── 2 word_work (write a sentence using the word) ─────────────────────────
    ww_pool = all_words[15:] if len(all_words) > 15 else all_words
    if len(ww_pool) < 2:
        ww_pool = all_words
    ww_words = random.sample(ww_pool, min(2, len(ww_pool)))
    word_work_questions: list[dict] = []
    for w in ww_words:
        word_work_questions.append({
            "id":           w.id + 30000,
            "type":         "word_work",
            "domain_num":   None,
            "domain_title": "",
            "lesson_title": "",
            "question_text": f'Write a sentence using the word "{w.word}".',
            "word":         w.word,
            "hint":         w.definition or "",
        })

    # ── Combine: vocab_mc first, then Q&A, then word_work ────────────────────
    questions = vocab_mc_questions + qa_questions + word_work_questions

    return {
        "grade":     grade,
        "questions": questions,
    }


@router.get("/grade-final-test/status")
# @tag ACADEMY CKLA
def get_grade_final_test_status(grade: int = Query(3), db: Session = Depends(get_db)):
    """Check if grade final test is locked (24h cooldown after a failed attempt)."""
    cooldown_key = f"ckla_final_test_last_fail_grade_{grade}"
    cfg = db.query(AppConfig).filter_by(key=cooldown_key).first()
    if cfg and cfg.value:
        try:
            last_fail = datetime.fromisoformat(cfg.value)
            retry_after = last_fail + timedelta(hours=24)
            if datetime.now() < retry_after:
                return {"locked": True, "retry_after": retry_after.isoformat(timespec="seconds")}
        except ValueError:
            pass
    return {"locked": False, "retry_after": None}


@router.post("/grade-final-test/submit")
# @tag ACADEMY CKLA XP
async def submit_grade_final_test(
    req: GradeFinalTestSubmit,
    grade: int = Query(3),
    db: Session = Depends(get_db),
):
    """Grade 27 final test answers by ID range, award XP on pass (>=80%).

    ID routing:
      qid < 10000        → Q&A         → AI graded (score 0/1/2; correct = 2)
      10000 <= qid < 20000 → vocab_mc  → local exact match
      30000 <= qid       → word_work   → difflib similarity >= 0.80

    Failed attempts are locked for 24 hours before retry.
    """
    # 24h cooldown guard
    cooldown_key = f"ckla_final_test_last_fail_grade_{grade}"
    cfg = db.query(AppConfig).filter_by(key=cooldown_key).first()
    if cfg and cfg.value:
        try:
            last_fail = datetime.fromisoformat(cfg.value)
            retry_after = last_fail + timedelta(hours=24)
            if datetime.now() < retry_after:
                raise HTTPException(
                    status_code=429,
                    detail=f"Please wait until {retry_after.isoformat(timespec='seconds')} before retrying.",
                )
        except ValueError:
            pass

    total = len(req.answers)
    if total == 0:
        raise HTTPException(status_code=400, detail="No answers submitted")

    correct = 0
    results: list[dict] = []
    wrong_questions: list[dict] = []

    for qid_str, user_ans in req.answers.items():
        try:
            qid = int(qid_str)
        except ValueError:
            continue

        user_ans_stripped = (user_ans or "").strip()

        if qid >= 30000:
            # word_work — student must write an original sentence using the focus word.
            # Reject (score=0) if the sentence copies the hint (definition or example_1)
            # with ≥80% similarity — mirrors the lesson Word Work tab logic exactly.
            # Also reject if the answer is too short to be a real sentence (< 8 chars).
            word = db.query(USAcademyWord).filter_by(id=qid - 30000).first()
            if not word:
                results.append({"question_id": qid, "score": 0, "type": "word_work"})
                continue
            hint_texts = [
                p.strip() for p in [word.definition or "", word.example_1 or ""]
                if p.strip()
            ]
            ans_lower = user_ans_stripped.lower()
            copied_hint = any(
                SequenceMatcher(None, ans_lower, h.lower()).ratio() >= 0.8
                for h in hint_texts
            )
            is_correct = (not copied_hint) and len(user_ans_stripped) >= 8
            score = 2 if is_correct else 0
            if score == 2:
                correct += 1
            else:
                wrong_questions.append({
                    "type":          "word_work",
                    "lesson_title":  "Vocabulary",
                    "question_text": f'Write a sentence using "{word.word}".',
                    "correct_answer": word.definition or word.word,
                })
            results.append({"question_id": qid, "score": score, "type": "word_work"})

        elif qid >= 10000:
            # vocab_mc — case-insensitive exact match
            word = db.query(USAcademyWord).filter_by(id=qid - 10000).first()
            is_correct = bool(word and user_ans_stripped.lower() == (word.word or "").lower())
            score = 2 if is_correct else 0
            if score == 2:
                correct += 1
            else:
                wrong_questions.append({
                    "type":          "vocab_mc",
                    "lesson_title":  "Vocabulary",
                    "question_text": word.definition if word else "",
                    "correct_answer": word.word if word else "",
                })
            results.append({"question_id": qid, "score": score, "type": "vocab_mc"})

        else:
            # Q&A — AI graded
            question = db.query(CKLAQuestion).filter_by(id=qid).first()
            if not question:
                results.append({"question_id": qid, "score": 0, "type": "qa"})
                continue
            lesson = db.query(CKLALesson).filter_by(id=question.lesson_id).first()
            passage = lesson.passage if lesson else ""
            try:
                result = await grade_answer(
                    question_text=question.question_text,
                    kind=question.kind,
                    model_answer=question.model_answer or "",
                    passage=passage,
                    user_answer=user_ans_stripped,
                )
                score = result.score
            except Exception:
                score = 0
            if score == 2:
                correct += 1
            else:
                wrong_questions.append({
                    "type":          "qa",
                    "lesson_title":  lesson.title if lesson else "",
                    "question_text": question.question_text,
                    "correct_answer": question.model_answer or "",
                })
            results.append({"question_id": qid, "score": score, "type": "qa"})

    pct = round(correct / total * 100) if total else 0
    _gpct_cfg = db.query(AppConfig).filter_by(key="ckla_grade_pass_pct").first()
    _grade_pass_pct = int(_gpct_cfg.value) if _gpct_cfg and _gpct_cfg.value else 80
    passed = pct >= _grade_pass_pct

    xp_awarded = 0
    retry_after_str: str | None = None
    if passed:
        xp_awarded = award_xp(db, "ckla_grade_final_pass", detail=f"grade_{grade}")
        if cfg:
            cfg.value = ""
    else:
        now_str = datetime.now().isoformat(timespec="seconds")
        if cfg:
            cfg.value = now_str
        else:
            db.add(AppConfig(key=cooldown_key, value=now_str))
        retry_after_str = (datetime.now() + timedelta(hours=24)).isoformat(timespec="seconds")

    db.commit()

    return {
        "grade":           grade,
        "total":           total,
        "correct":         correct,
        "score_pct":       pct,
        "passed":          passed,
        "xp_awarded":      xp_awarded,
        "results":         results,
        "retry_after":     retry_after_str,
        "wrong_questions": wrong_questions,
    }


# ── Spelling / Grammar / Morphology ──────────────────────────────────────────

@router.get("/spelling/{unit}")
def get_spelling(unit: int, db: Session = Depends(get_db)):
    """Return all spelling weeks for a unit.

    Each week: {week, pattern, words: [], challenge_words: []}
    """
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
