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

from datetime import date as _date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

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

    for item in study_items:
        existing = db.query(WordReview).filter(WordReview.study_item_id == item.id).first()
        if existing:
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


# @tag REVIEW @tag SM2
@router.get("/api/review/today")
def get_today_reviews(db: Session = Depends(get_db)):
    """Return all words due for review today (next_review <= today)."""
    today_str = _date.today().isoformat()

    reviews = (
        db.query(WordReview)
        .filter(WordReview.next_review <= today_str)
        .order_by(WordReview.next_review)
        .all()
    )

    result = []
    for wr in reviews:
        item = db.query(StudyItem).filter(StudyItem.id == wr.study_item_id).first()
        if not item:
            continue
        result.append({
            "review_id":      wr.id,
            "study_item_id":  wr.study_item_id,
            "word":           wr.word,
            "subject":        wr.subject,
            "textbook":       wr.textbook,
            "lesson":         wr.lesson,
            "question":       item.question,
            "answer":         item.answer,
            "hint":           item.hint,
            "extra_data":     item.extra_data,
            "easiness":       float(wr.easiness),
            "interval":       wr.interval,
            "repetitions":    wr.repetitions,
            "total_reviews":  wr.total_reviews,
            "total_correct":  wr.total_correct,
        })

    return {"date": today_str, "count": len(result), "reviews": result}


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

    wr.repetitions  = new_reps
    wr.easiness     = str(round(new_ease, 2))
    wr.interval     = new_interval
    wr.next_review  = next_date.isoformat()
    wr.last_review  = _date.today().isoformat()
    wr.total_reviews = (wr.total_reviews or 0) + 1
    if req.is_correct:
        wr.total_correct = (wr.total_correct or 0) + 1

    db.commit()
    db.refresh(wr)

    return {
        "review_id":    wr.id,
        "word":         wr.word,
        "quality":      quality,
        "new_easiness": float(wr.easiness),
        "new_interval": wr.interval,
        "next_review":  wr.next_review,
        "repetitions":  wr.repetitions,
    }


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
