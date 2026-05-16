"""
routers/ckla_progress.py — CKLA lesson progress, Q&A grading, and badge endpoints (7 endpoints).
Section: Academy
Dependencies: models/ckla, models/us_academy, models/gamification, services/ckla_grader, services/xp_engine, services/streak_engine, services/island_care_engine
API endpoints:
  GET  /api/academy/ckla/lessons/{lesson_id}/progress
  POST /api/academy/ckla/lessons/{lesson_id}/progress
  POST /api/academy/ckla/lessons/{lesson_id}/difficulty
  POST /api/academy/ckla/questions/{question_id}/answer
  GET  /api/academy/ckla/badges
  POST /api/academy/ckla/badges/check

Catalog / content → ckla.py
Domain Test       → ckla_domain_test.py
Grade Final Test  → ckla_grade_test.py
Shared helpers    → _ckla_common.py
"""
import logging
from datetime import date as _date, timedelta
from difflib import SequenceMatcher

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from backend.database import get_db
from backend.models.ckla import (
    CKLADomain, CKLALesson, CKLAQuestion,
    CKLAWordLesson, CKLALessonProgress, CKLAQuestionResponse,
    CKLABadge, CKLAUserBadge,
)
from backend.models.us_academy import USAcademyWord
from backend.models import WordReview
from backend.models.system import AppConfig
from backend.models.gamification import XPLog
from backend.services.ckla_grader import grade_answer
from backend.services.xp_engine import award_xp
from backend.services.streak_engine import mark_ckla_done
from backend.services.island_care_engine import apply_subject_gain as _island_apply_gain
from backend.routers._ckla_common import (
    _CFG_DAILY_GOAL,
    NOW,
    ProgressUpdate, DifficultyRating, AnswerSubmit,
    _get_or_create_progress, _progress_dict, _badge_dict,
)

router = APIRouter(prefix="/api/academy/ckla", tags=["ckla"])


# ── Lesson Progress ────────────────────────────────────────────────────────────

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
    All four tabs done (first time) → XP ckla_lesson_complete + mark_ckla_done (streak).
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

            source_ref = f"lesson_{lesson_id}"
            word_map = {
                w.id: w for w in
                db.query(USAcademyWord).filter(USAcademyWord.id.in_(word_ids)).all()
            }
            word_names = [word_map[wid].word for wid in word_ids if wid in word_map]
            existing_words = {
                row.word for row in
                db.query(WordReview.word)
                .filter(
                    WordReview.source == "ckla",
                    WordReview.source_ref == source_ref,
                    WordReview.word.in_(word_names),
                ).all()
            }
            for wid in word_ids:
                if wid not in word_map:
                    continue
                w = word_map[wid]
                if w.word in existing_words:
                    continue
                db.add(WordReview(
                    study_item_id=None,
                    word=w.word,
                    subject="English",
                    textbook="CKLA",
                    lesson=str(lesson_id),
                    easiness=2.5,
                    interval=0,
                    repetitions=0,
                    next_review=tomorrow,
                    last_review="",
                    total_reviews=0,
                    total_correct=0,
                    source="ckla",
                    source_ref=source_ref,
                    question=w.definition or "",
                    hint=w.example_1 or "",
                ))

        if req.qa_done is True and not prog.qa_done:
            prog.qa_done = True

        if req.word_work_done is True and not prog.word_work_done:
            if not req.word_work_answer or not req.word_work_answer.strip():
                raise HTTPException(
                    status_code=400,
                    detail="Word work answer is required.",
                )
            if req.word_work_answer and lesson.word_work_word:
                typed_lower = req.word_work_answer.strip().lower()
                word_lower  = lesson.word_work_word.strip().lower()
                if typed_lower == word_lower:
                    raise HTTPException(
                        status_code=400,
                        detail="Write a full sentence using the word, not just the word itself.",
                    )
                # Reject if answer ≥80% similar to hint — look up via ID-based join (reliable)
                _wlinks = db.query(CKLAWordLesson).filter_by(lesson_id=lesson.id).all()
                _linked_ids = [wl.word_id for wl in _wlinks]
                focus_word_rec = None
                if _linked_ids:
                    for _uw in db.query(USAcademyWord).filter(USAcademyWord.id.in_(_linked_ids)).all():
                        if (_uw.word or "").strip().lower() == word_lower:
                            focus_word_rec = _uw
                            break
                if focus_word_rec is None:
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
            award_xp(db, "ckla_lesson_complete", detail=str(lesson_id), commit=False)
            mark_ckla_done(db, commit=False)
            try:
                _island_apply_gain(db, "english", "english_stage")
            except Exception:
                pass

            today_str = _date.today().isoformat()
            daily_goal_cfg = db.query(AppConfig).filter_by(key=_CFG_DAILY_GOAL).first()
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
                already_awarded = db.query(XPLog).filter(
                    XPLog.action == "ckla_daily_goal",
                    XPLog.detail == today_str,
                ).first()
                if not already_awarded:
                    award_xp(db, "ckla_daily_goal", detail=today_str, commit=False)

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


# ── Q&A Answer ────────────────────────────────────────────────────────────────

@router.post("/questions/{question_id}/answer")
# @tag ACADEMY CKLA AI
async def submit_answer(
    question_id: int, req: AnswerSubmit, db: Session = Depends(get_db)
):
    """Submit an answer → AI grading → save result. Max 2 attempts per question (1 retry)."""
    question = db.query(CKLAQuestion).filter_by(id=question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    # Enforce 1-retry limit
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


# ── Badges ────────────────────────────────────────────────────────────────────

@router.get("/badges")
# @tag ACADEMY CKLA
def get_badges(grade: int = Query(3, ge=3, le=8), db: Session = Depends(get_db)):
    """Badge gallery: all badges with earned flag."""
    badges = db.query(CKLABadge).order_by(CKLABadge.condition_value).all()
    earned_map = {
        ub.badge_key: ub.earned_at
        for ub in db.query(CKLAUserBadge).all()
    }
    return [_badge_dict(b, earned_map.get(b.badge_key)) for b in badges]


@router.post("/badges/check")
# @tag ACADEMY CKLA XP
def check_and_award_badges(grade: int = Query(3, ge=3, le=8), db: Session = Depends(get_db)):
    """Check progress against badge conditions and award any newly earned badges.

    Returns list of newly awarded badge_keys (empty if none new).
    Bulk-loads all domains + lessons + completions to avoid N+1 queries.
    """
    newly_earned: list[dict] = []
    now = NOW()

    earned_keys = {ub.badge_key for ub in db.query(CKLAUserBadge).all()}
    badges = db.query(CKLABadge).all()

    # Bulk-load all domains + lesson IDs + completed lesson IDs
    all_domains = db.query(CKLADomain).filter_by(is_active=True).all()
    domain_by_num_grade: dict[tuple, CKLADomain] = {(d.domain_num, d.grade): d for d in all_domains}

    all_lessons = db.query(CKLALesson.id, CKLALesson.domain_id).filter_by(is_active=True).all()
    domain_lesson_ids: dict[int, list[int]] = {}
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
