"""
routers/review.py — SM-2 spaced repetition review routes
Section: English
Dependencies: database, models, sm2
API:
  POST /api/review/register-lesson
  GET  /api/review/today
  POST /api/review/result
  GET  /api/review/stats
"""

import logging
from datetime import date as _date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from backend.database import get_db
from backend.models import StudyItem, WordReview
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
                easiness="2.5",
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
def get_today_reviews(db: Session = Depends(get_db)):
    """Return all words due for review today across Academy/Daily/My sources."""
    today_str = _date.today().isoformat()

    reviews = (
        db.query(WordReview)
        .filter(WordReview.next_review <= today_str)
        .order_by(WordReview.next_review)
        .all()
    )

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
            "easiness":       float(wr.easiness),
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
                easiness="2.5",
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
        easiness=float(wr.easiness),
        interval=wr.interval,
    )

    try:
        wr.repetitions   = new_reps
        wr.easiness      = str(round(new_ease, 2))
        wr.interval      = new_interval
        wr.next_review   = next_date.isoformat()
        wr.last_review   = _date.today().isoformat()
        wr.total_reviews = (wr.total_reviews or 0) + 1
        if req.is_correct:
            wr.total_correct = (wr.total_correct or 0) + 1

        db.commit()
        db.refresh(wr)

        island = {"xp_multiplier": 1.0}
        try:
            from backend.services import island_care_engine as _care
            today_str = _date.today().isoformat()
            due_remaining = db.query(WordReview).filter(WordReview.next_review <= today_str).count()
            if due_remaining == 0:
                island = _care.apply_subject_gain(db, "review", "review")
        except Exception:
            pass

        return {
            "review_id":    wr.id,
            "word":         wr.word,
            "quality":      quality,
            "new_easiness": float(wr.easiness),
            "new_interval": wr.interval,
            "next_review":  wr.next_review,
            "repetitions":  wr.repetitions,
            "island":       island,
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
                "easiness":      float(w.easiness),
                "interval":      w.interval,
                "total_reviews": w.total_reviews,
                "accuracy":      round(w.total_correct / max(1, w.total_reviews) * 100),
            }
            for w in struggling
        ],
    }
