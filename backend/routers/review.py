"""
routers/review.py — SM-2 spaced repetition review routes
Section: English / CKLA (shared SM-2 infrastructure)
Dependencies: database, models, sm2
API:
  POST /api/review/register-lesson
  GET  /api/review/today            — optional ?source=ckla|daily|my|academy
  POST /api/review/result           — per-word SM-2 update only (no XP/streak)
  GET  /api/review/stats
  GET  /api/review/hub-status       — english + math due counts for Review Hub
  POST /api/review/session-complete — award XP + streak when a session finishes
"""

import logging
from datetime import date as _date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, and_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from backend.database import get_db
from backend.models import StudyItem, WordReview, XPLog
from backend.sm2 import sm2_calculate, quality_from_result

router = APIRouter()


# ── Pydantic Schemas ───────────────────────────────────────

class RegisterLessonReviewRequest(BaseModel):
    subject: str
    textbook: str
    lesson: str


class ReviewResultRequest(BaseModel):
    review_id: int
    is_correct: bool
    attempts: int = 1


class WordEntry(BaseModel):
    word: str
    question: str = ""   # meaning
    hint: str = ""       # example sentence


class RegisterWordsRequest(BaseModel):
    """Register Daily Words / My Words into the unified SM-2 queue."""
    source: str                   # 'daily' | 'my'
    source_ref: str = ""          # e.g. 'grade_3/week_2' or list name
    words: list[WordEntry]


class SessionCompleteRequest(BaseModel):
    type: str  # 'english' | 'math'


# ── Routes ─────────────────────────────────────────────────

# @tag REVIEW @tag SM2
@router.post("/api/review/register-lesson")
def register_lesson_for_review(
    req: RegisterLessonReviewRequest,
    db: Session = Depends(get_db),
):
    """Register all words from a completed lesson into the SM-2 review system."""
    study_items = (
        db.query(StudyItem)
        .filter(
            StudyItem.subject == req.subject,
            StudyItem.textbook == req.textbook,
            StudyItem.lesson == req.lesson,
        )
        .all()
    )
    if not study_items:
        raise HTTPException(status_code=404, detail="No study items found for this lesson")

    tomorrow = (_date.today() + timedelta(days=1)).isoformat()
    registered = 0

    item_ids = [item.id for item in study_items]
    existing_ids = {
        row.study_item_id
        for row in db.query(WordReview.study_item_id)
        .filter(WordReview.study_item_id.in_(item_ids))
        .all()
    }

    try:
        for item in study_items:
            if item.id in existing_ids:
                continue
            wr = WordReview(
                study_item_id=item.id,
                word=item.answer or "",
                subject=req.subject,
                textbook=req.textbook,
                lesson=req.lesson,
                easiness=2.5,
                interval=0,
                repetitions=0,
                next_review=tomorrow,
                last_review="",
                total_reviews=0,
                total_correct=0,
            )
            db.add(wr)
            registered += 1

        db.commit()
        return {"registered": registered, "total_items": len(study_items), "lesson": req.lesson}
    except SQLAlchemyError as e:
        db.rollback()
        logger.error("register_lesson_for_review failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to register lesson for review")


# @tag REVIEW @tag SM2
@router.get("/api/review/today")
def get_today_reviews(
    source: Optional[str] = Query(None, description="Filter by source: ckla|daily|my|academy"),
    db: Session = Depends(get_db),
):
    """Return all words due for review today across Academy/Daily/My/CKLA sources.

    Optional ?source= query param to filter by a single source type.
    """
    today_str = _date.today().isoformat()

    q = db.query(WordReview).filter(WordReview.next_review <= today_str)
    if source:
        q = q.filter(WordReview.source == source)
    reviews = q.order_by(WordReview.next_review).all()

    academy_ids = [wr.study_item_id for wr in reviews
                   if (wr.source or "academy") == "academy" and wr.study_item_id]
    items_by_id = {
        item.id: item
        for item in db.query(StudyItem).filter(StudyItem.id.in_(academy_ids)).all()
    }

    result = []
    for wr in reviews:
        src = wr.source or "academy"
        if src == "academy":
            item = items_by_id.get(wr.study_item_id)
            if not item:
                continue  # orphaned academy row — skip
            question, answer, hint, extra = item.question, item.answer, item.hint, item.extra_data
        else:
            question, answer, hint, extra = (wr.question or ""), wr.word, (wr.hint or ""), ""

        result.append({
            "review_id":      wr.id,
            "study_item_id":  wr.study_item_id,
            "word":           wr.word,
            "source":         src,
            "source_ref":     wr.source_ref or "",
            "subject":        wr.subject,
            "textbook":       wr.textbook,
            "lesson":         wr.lesson,
            "question":       question,
            "answer":         answer,
            "hint":           hint,
            "extra_data":     extra,
            "easiness":       wr.easiness,
            "interval":       wr.interval,
            "repetitions":    wr.repetitions,
            "total_reviews":  wr.total_reviews,
            "total_correct":  wr.total_correct,
        })

    return {"date": today_str, "count": len(result), "reviews": result}


# @tag REVIEW @tag SM2 @tag DAILY_WORDS @tag MY_WORDS
@router.post("/api/review/register-words")
def register_words_for_review(req: RegisterWordsRequest, db: Session = Depends(get_db)):
    """Register Daily Words / My Words into the unified SM-2 queue.

    De-duplicates by (source, source_ref, word) so re-completing a Daily Words
    day won't re-insert rows.
    """
    if req.source not in ("daily", "my"):
        raise HTTPException(status_code=400, detail="source must be 'daily' or 'my'")

    tomorrow = (_date.today() + timedelta(days=1)).isoformat()
    words_in_req = [w.word for w in req.words if w.word]
    existing_words = {
        row.word for row in
        db.query(WordReview.word)
        .filter(
            WordReview.source == req.source,
            WordReview.source_ref == (req.source_ref or ""),
            WordReview.word.in_(words_in_req),
        ).all()
    }

    try:
        registered = 0
        for w in req.words:
            if not w.word or w.word in existing_words:
                continue
            wr = WordReview(
                study_item_id=None,
                word=w.word,
                subject="English",
                textbook="",
                lesson="",
                easiness=2.5,
                interval=0,
                repetitions=0,
                next_review=tomorrow,
                last_review="",
                total_reviews=0,
                total_correct=0,
                source=req.source,
                question=w.question or "",
                hint=w.hint or "",
                source_ref=req.source_ref or "",
            )
            db.add(wr)
            registered += 1

        db.commit()
        return {"registered": registered, "source": req.source, "source_ref": req.source_ref}
    except SQLAlchemyError as e:
        db.rollback()
        logger.error("register_words_for_review failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to register words for review")


# @tag REVIEW @tag SM2
@router.post("/api/review/result")
def submit_review_result(req: ReviewResultRequest, db: Session = Depends(get_db)):
    """Submit a review result and run the SM-2 algorithm to reschedule the word."""
    wr = db.query(WordReview).filter(WordReview.id == req.review_id).first()
    if not wr:
        raise HTTPException(status_code=404, detail=f"Review id={req.review_id} not found")

    quality = quality_from_result(req.is_correct, req.attempts)

    new_reps, new_ease, new_interval, next_date = sm2_calculate(
        quality=quality,
        repetitions=wr.repetitions,
        easiness=wr.easiness,
        interval=wr.interval,
    )

    try:
        wr.repetitions   = new_reps
        wr.easiness      = round(new_ease, 2)
        wr.interval      = new_interval
        wr.next_review   = next_date.isoformat()
        wr.last_review   = _date.today().isoformat()
        wr.total_reviews = (wr.total_reviews or 0) + 1
        if req.is_correct:
            wr.total_correct = (wr.total_correct or 0) + 1

        db.commit()
        db.refresh(wr)

        return {
            "review_id":    wr.id,
            "word":         wr.word,
            "quality":      quality,
            "new_easiness": wr.easiness,
            "new_interval": wr.interval,
            "next_review":  wr.next_review,
            "repetitions":  wr.repetitions,
        }
    except SQLAlchemyError as e:
        db.rollback()
        logger.error("submit_review_result failed for review_id=%s: %s", req.review_id, e)
        raise HTTPException(status_code=500, detail="Failed to save review result")


# @tag REVIEW @tag SM2 @tag STATS
@router.get("/api/review/stats")
def get_review_stats(db: Session = Depends(get_db)):
    """Return overall SM-2 review statistics including struggling words."""
    today_str = _date.today().isoformat()

    total     = db.query(WordReview).count()
    due_today = db.query(WordReview).filter(WordReview.next_review <= today_str).count()
    mastered  = db.query(WordReview).filter(WordReview.repetitions >= 5).count()

    struggling = (
        db.query(WordReview)
        .filter(WordReview.total_reviews > 0)
        .order_by(WordReview.easiness)
        .limit(10)
        .all()
    )

    return {
        "total_words":  total,
        "due_today":    due_today,
        "mastered":     mastered,
        "learning":     total - mastered,
        "struggling_words": [
            {
                "word":          w.word,
                "easiness":      w.easiness,
                "interval":      w.interval,
                "total_reviews": w.total_reviews,
                "accuracy":      round(w.total_correct / max(1, w.total_reviews) * 100),
            }
            for w in struggling
        ],
    }


# @tag REVIEW @tag HOME_DASHBOARD
@router.get("/api/review/hub-status")
def get_hub_status(db: Session = Depends(get_db)):
    """Return due counts for the Review Hub (English SM-2 + CKLA SM-2 + Math spaced review)."""
    today_str      = _date.today().isoformat()
    seven_days_ago = (_date.today() - timedelta(days=7)).isoformat()

    due_q = db.query(WordReview).filter(WordReview.next_review <= today_str)

    # CKLA reviews are tracked separately from general English/DUX reviews
    ckla_due    = due_q.filter(WordReview.source == "ckla").count()
    english_due = due_q.filter(WordReview.source != "ckla").count()

    breakdown_rows = (
        db.query(WordReview.source, func.count(WordReview.id))
        .filter(WordReview.next_review <= today_str, WordReview.source != "ckla")
        .group_by(WordReview.source)
        .all()
    )
    breakdown = {(src or "academy"): cnt for src, cnt in breakdown_rows}

    math_due = 0
    math_accuracy_7d = None
    try:
        from backend.models.math import MathSpacedReview as _MSR
        math_due = db.query(_MSR).filter(_MSR.next_review_date <= today_str).count()
        # Average exit_quiz_score (out of 5) for lessons reviewed in last 7 days
        _math_acc_row = (
            db.query(func.avg(_MSR.exit_quiz_score))
            .filter(
                _MSR.last_reviewed_at >= seven_days_ago,
                _MSR.exit_quiz_score.isnot(None),
            )
            .scalar()
        )
        if _math_acc_row is not None:
            math_accuracy_7d = round(_math_acc_row / 5 * 100)
    except Exception:
        pass

    # Detect sessions completed today via XPLog
    english_done_today = db.query(XPLog).filter(
        XPLog.action == "review_complete",
        XPLog.created_at >= today_str,
    ).first() is not None
    math_done_today = db.query(XPLog).filter(
        XPLog.action == "math_spaced_review",
        XPLog.created_at >= today_str,
    ).first() is not None
    ckla_done_today = db.query(XPLog).filter(
        XPLog.action == "ckla_review_complete",
        XPLog.created_at >= today_str,
    ).first() is not None

    # 7-day accuracy for English (words last reviewed in the past 7 days)
    acc_row = (
        db.query(
            func.sum(WordReview.total_correct),
            func.sum(WordReview.total_reviews),
        )
        .filter(
            and_(
                WordReview.source != "ckla",
                WordReview.last_review >= seven_days_ago,
                WordReview.total_reviews > 0,
            )
        )
        .first()
    )
    if acc_row and acc_row[1]:
        english_accuracy_7d = round(acc_row[0] / acc_row[1] * 100)
    else:
        english_accuracy_7d = None

    total_items = english_due + math_due + ckla_due
    est_minutes = max(1, round((english_due * 30 + ckla_due * 30 + math_due * 90) / 60)) if total_items else 0

    return {
        "english": {
            "due":             english_due,
            "breakdown":       breakdown,
            "completed_today": english_done_today,
            "accuracy_7d":     english_accuracy_7d,
        },
        "math": {
            "due":             math_due,
            "completed_today": math_done_today,
            "accuracy_7d":     math_accuracy_7d,
        },
        "ckla": {
            "due":             ckla_due,
            "completed_today": ckla_done_today,
        },
        "total_due":         total_items,
        "all_done":          total_items == 0,
        "estimated_minutes": est_minutes,
    }


# @tag REVIEW @tag XP @tag STREAK
@router.post("/api/review/session-complete")
def complete_review_session(req: SessionCompleteRequest, db: Session = Depends(get_db)):
    """Called by Review Hub when a full English or Math review session ends.

    Awards XP and updates streak for the completed session type.
    When both English and Math queues are empty, triggers island care gain.
    """
    if req.type not in ("english", "math", "ckla"):
        raise HTTPException(status_code=400, detail="type must be 'english', 'math', or 'ckla'")

    today_str = _date.today().isoformat()
    xp_earned = 0

    if req.type == "english":
        try:
            from backend.services import xp_engine as _xp
            xp_earned = _xp.award_xp(db, "review_complete")
        except Exception as e:
            logger.warning("review_complete XP failed: %s", e)
        try:
            from backend.services import streak_engine as _streak
            _streak.mark_review_done(db)
        except Exception as e:
            logger.warning("mark_review_done failed: %s", e)

    elif req.type == "math":
        try:
            from backend.services import xp_engine as _xp
            xp_earned = _xp.award_xp(db, "math_spaced_review")
        except Exception as e:
            logger.warning("math_spaced_review XP failed: %s", e)
        try:
            from backend.services import streak_engine as _streak
            _streak.mark_math_done(db)
        except Exception as e:
            logger.warning("mark_math_done failed: %s", e)

    elif req.type == "ckla":
        try:
            from backend.services import xp_engine as _xp
            xp_earned = _xp.award_xp(db, "ckla_review_complete")
        except Exception as e:
            logger.warning("ckla_review_complete XP failed: %s", e)

    # Check if all queues are now empty → island care
    english_due = db.query(WordReview).filter(
        WordReview.next_review <= today_str,
        WordReview.source != "ckla",
    ).count()
    math_due = 0
    try:
        from backend.models.math import MathSpacedReview as _MSR
        math_due = db.query(_MSR).filter(_MSR.next_review_date <= today_str).count()
    except Exception:
        pass

    ckla_due = db.query(WordReview).filter(
        WordReview.next_review <= today_str,
        WordReview.source == "ckla",
    ).count()

    island = {"xp_multiplier": 1.0}
    all_done = english_due == 0 and math_due == 0 and ckla_due == 0
    if all_done:
        try:
            from backend.services import island_care_engine as _care
            island = _care.apply_subject_gain(db, "review", "review")
        except Exception:
            pass

    return {
        "type":      req.type,
        "xp_earned": xp_earned,
        "island":    island,
        "all_done":  all_done,
    }
