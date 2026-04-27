"""
routers/progress.py — Progress tracking and answer verification routes
Section: English
Dependencies: database, models
API:
  POST /api/progress/sparta_reset
  POST /api/progress/challenge_complete
  POST /api/progress/verify
"""

import logging
import re as _re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from backend.database import get_db
from backend.models import StudyItem, Progress

router = APIRouter()


# ── Pydantic Schemas ───────────────────────────────────────

class SubjectLesson(BaseModel):
    subject: str
    textbook: str = ""
    lesson: str


class VerifyRequest(BaseModel):
    subject: str
    textbook: str = ""
    lesson: str
    item_id: int
    user_input: str

    def clean(self):
        """Sanitize user input."""
        self.user_input = self.user_input.strip()[:300]
        return self


# ── Routes ─────────────────────────────────────────────────

# @tag PROGRESS @tag SPARTA
@router.post("/api/progress/sparta_reset")
def sparta_reset_progress(req: SubjectLesson, db: Session = Depends(get_db)):
    """Reset streak index to 0 on Perfect Challenge failure."""
    progress = (
        db.query(Progress)
        .filter(
            Progress.subject == req.subject,
            Progress.textbook == req.textbook,
            Progress.lesson == req.lesson,
        )
        .first()
    )
    try:
        if progress:
            progress.current_index = 0
            db.commit()
        return {"status": "reset"}
    except SQLAlchemyError as e:
        db.rollback()
        logger.error("sparta_reset_progress failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to reset progress")


# @tag PROGRESS @tag CHALLENGE
@router.post("/api/progress/challenge_complete")
def challenge_perfect_complete(req: SubjectLesson, db: Session = Depends(get_db)):
    """Update best_streak on a no-miss challenge completion."""
    progress = (
        db.query(Progress)
        .filter(
            Progress.subject == req.subject,
            Progress.textbook == req.textbook,
            Progress.lesson == req.lesson,
        )
        .first()
    )
    n = (
        db.query(StudyItem)
        .filter(
            StudyItem.subject == req.subject,
            StudyItem.textbook == req.textbook,
            StudyItem.lesson == req.lesson,
        )
        .count()
    )
    try:
        if not progress:
            progress = Progress(
                subject=req.subject, textbook=req.textbook, lesson=req.lesson,
                current_index=0, best_streak=0,
            )
            db.add(progress)
            db.commit()
            db.refresh(progress)
        progress.best_streak = max(progress.best_streak or 0, n)
        progress.current_index = 0
        db.commit()
        db.refresh(progress)
        return {"best_streak": progress.best_streak}
    except SQLAlchemyError as e:
        db.rollback()
        logger.error("challenge_perfect_complete failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to update challenge progress")


# @tag PROGRESS @tag VERIFY
@router.post("/api/progress/verify")
def verify_answer(req: VerifyRequest, db: Session = Depends(get_db)):
    """Check user's answer against the correct answer and update streak progress."""
    req.clean()
    item = db.query(StudyItem).filter(StudyItem.id == req.item_id).first()
    progress = (
        db.query(Progress)
        .filter(
            Progress.subject == req.subject,
            Progress.textbook == req.textbook,
            Progress.lesson == req.lesson,
        )
        .first()
    )

    if not item or not progress:
        raise HTTPException(status_code=404, detail="Data not found")

    is_correct = req.user_input.strip().lower() == item.answer.strip().lower()

    try:
        if is_correct:
            progress.current_index += 1
            if progress.current_index > progress.best_streak:
                progress.best_streak = progress.current_index
        else:
            progress.current_index = 0

        db.commit()
        db.refresh(progress)
        return {
            "is_correct":     is_correct,
            "correct_answer": item.answer,
            "current_index":  progress.current_index,
            "best_streak":    progress.best_streak,
        }
    except SQLAlchemyError as e:
        db.rollback()
        logger.error("verify_answer failed for item_id=%s: %s", req.item_id, e)
        raise HTTPException(status_code=500, detail="Failed to save answer result")
