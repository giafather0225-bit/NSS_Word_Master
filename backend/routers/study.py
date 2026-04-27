"""
routers/study.py — Study session data and learning analytics logging routes
Section: English
Dependencies: database, models, voca_sync
API:
  GET  /api/study/{subject}/{textbook}/{lesson}
  POST /api/learning/log
  POST /api/learning/word-attempt
  POST /api/learning/word-attempts-batch
"""

import json
import logging
import re as _re
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text as _text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from backend.database import get_db, LEARNING_ROOT
from backend.models import StudyItem, Progress
from backend.schemas_common import Str30, Str50, Str100
from backend.utils import validate_lesson as _validate_lesson
from backend.voca_sync import load_lesson_json, sync_lesson_to_db
from backend.services import academy_session as academy_sess

router = APIRouter()


# _validate_lesson → backend/utils.py


def serialize_item(row: StudyItem) -> dict:
    """Serialize a StudyItem ORM row to a plain dict."""
    return {
        "id": row.id,
        "subject": row.subject,
        "textbook": row.textbook,
        "lesson": row.lesson,
        "question": row.question,
        "answer": row.answer,
        "hint": row.hint,
        "extra_data": row.extra_data,
    }


# ── Pydantic Schemas ───────────────────────────────────────

class LearningLogCreate(BaseModel):
    textbook: Str100 = ""
    lesson: Str100 = ""
    stage: Str50 = ""
    word_count: int = 0
    correct_count: int = 0
    wrong_words: list = []
    started_at: Str30 = ""
    completed_at: Str30 = ""
    duration_sec: int = 0

    def clean(self):
        """Clamp negatives to 0 (strings validated by Pydantic — 422 on overflow)."""
        if self.duration_sec < 0:
            self.duration_sec = 0
        if self.word_count < 0:
            self.word_count = 0
        if self.correct_count < 0:
            self.correct_count = 0


class WordAttemptCreate(BaseModel):
    study_item_id: int | None = None
    textbook: str = ""
    lesson: str = ""
    word: str = ""
    stage: str = ""
    is_correct: bool = False
    user_answer: str = ""
    attempted_at: str = ""

    def clean(self):
        """Sanitize all string fields."""
        self.textbook = self.textbook.strip()[:100]
        self.lesson = self.lesson.strip()[:100]
        self.word = self.word.strip()[:200]
        self.stage = self.stage.strip()[:50]
        self.user_answer = self.user_answer.strip()[:500]
        self.attempted_at = self.attempted_at.strip()[:30]


class WordAttemptsBatch(BaseModel):
    attempts: list[WordAttemptCreate] = []

    def clean(self):
        """Sanitize all attempt records."""
        for a in self.attempts:
            a.clean()


# ── Routes ─────────────────────────────────────────────────

# @tag STUDY
@router.get("/api/study/{subject}/{textbook}/{lesson}")
def get_study_data(subject: str, textbook: str, lesson: str, db: Session = Depends(get_db)):
    """Return study items and progress for a lesson; auto-syncs from data.json if DB is empty."""
    from backend.utils import validate_name as _validate_name
    subject = _validate_name(subject, "subject")
    lesson  = _validate_lesson(lesson)
    rows = (
        db.query(StudyItem)
        .filter(
            StudyItem.subject == subject,
            StudyItem.textbook == textbook,
            StudyItem.lesson == lesson,
        )
        .order_by(StudyItem.id)
        .all()
    )

    # Auto-sync from disk if DB is empty
    if not rows:
        lesson_dir = LEARNING_ROOT / subject / textbook / lesson
        jrows = load_lesson_json(lesson_dir.parent, lesson)
        if jrows:
            # Legacy disk auto-sync: on-disk data.json may predate the
            # definition-validation rules, so allow entries without definitions.
            sync_lesson_to_db(
                db, lesson_dir.parent, lesson, jrows,
                subject=subject, textbook=textbook,
                require_definition=False,
            )
            rows = (
                db.query(StudyItem)
                .filter(
                    StudyItem.subject == subject,
                    StudyItem.textbook == textbook,
                    StudyItem.lesson == lesson,
                )
                .order_by(StudyItem.id)
                .all()
            )

    if not rows:
        return {"items": [], "progress": {"current_index": 0, "best_streak": 0}}

    progress = (
        db.query(Progress)
        .filter(
            Progress.subject == subject,
            Progress.textbook == textbook,
            Progress.lesson == lesson,
        )
        .first()
    )
    if not progress:
        progress = Progress(subject=subject, textbook=textbook, lesson=lesson, current_index=0, best_streak=0)
        db.add(progress)
        db.commit()
        db.refresh(progress)

    # @tag ACADEMY — ensure an in-progress AcademySession tracks this lesson
    academy_sess.upsert_session(db, subject, textbook, lesson)

    return {"items": [serialize_item(r) for r in rows], "progress": progress}


# @tag STUDY @tag ANALYTICS
@router.post("/api/learning/log")
def save_learning_log(body: LearningLogCreate, db: Session = Depends(get_db)):
    """Save a stage completion log entry to the learning_logs table."""
    body.clean()
    try:
        db.execute(
            _text(
                "INSERT INTO learning_logs "
                "(textbook, lesson, stage, word_count, correct_count, "
                " wrong_words_json, started_at, completed_at, duration_sec) "
                "VALUES (:textbook, :lesson, :stage, :word_count, :correct_count, "
                " :wrong_words, :started_at, :completed_at, :duration_sec)"
            ),
            {
                "textbook":      body.textbook,
                "lesson":        body.lesson,
                "stage":         body.stage,
                "word_count":    body.word_count,
                "correct_count": body.correct_count,
                "wrong_words":   json.dumps(body.wrong_words),
                "started_at":    body.started_at,
                "completed_at":  body.completed_at,
                "duration_sec":  body.duration_sec,
            },
        )
        db.commit()
        if body.textbook and body.lesson:
            academy_sess.touch_session(db, body.textbook, body.lesson, body.stage)
        return {"ok": True}
    except SQLAlchemyError as e:
        db.rollback()
        logger.error("save_learning_log failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to save learning log")


# @tag STUDY @tag ANALYTICS
@router.post("/api/learning/word-attempt")
def save_word_attempt(body: WordAttemptCreate, db: Session = Depends(get_db)):
    """Save a single word attempt (correct or wrong) to the word_attempts table."""
    body.clean()
    try:
        db.execute(
            _text(
                "INSERT INTO word_attempts "
                "(study_item_id, textbook, lesson, word, stage, is_correct, user_answer, attempted_at) "
                "VALUES (:study_item_id, :textbook, :lesson, :word, :stage, :is_correct, :user_answer, :attempted_at)"
            ),
            {
                "study_item_id": body.study_item_id,
                "textbook":      body.textbook,
                "lesson":        body.lesson,
                "word":          body.word,
                "stage":         body.stage,
                "is_correct":    1 if body.is_correct else 0,
                "user_answer":   body.user_answer,
                "attempted_at":  body.attempted_at,
            },
        )
        db.commit()
        return {"ok": True}
    except SQLAlchemyError as e:
        db.rollback()
        logger.error("save_word_attempt failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to save word attempt")


# @tag STUDY @tag ANALYTICS
@router.post("/api/learning/word-attempts-batch")
def save_word_attempts_batch(body: WordAttemptsBatch, db: Session = Depends(get_db)):
    """Save multiple word attempts in a single batch insert."""
    body.clean()
    if not body.attempts:
        return {"ok": True, "count": 0}
    try:
        db.execute(
            _text(
                "INSERT INTO word_attempts "
                "(study_item_id, textbook, lesson, word, stage, is_correct, user_answer, attempted_at) "
                "VALUES (:study_item_id, :textbook, :lesson, :word, :stage, :is_correct, :user_answer, :attempted_at)"
            ),
            [
                {
                    "study_item_id": a.study_item_id,
                    "textbook":      a.textbook,
                    "lesson":        a.lesson,
                    "word":          a.word,
                    "stage":         a.stage,
                    "is_correct":    1 if a.is_correct else 0,
                    "user_answer":   a.user_answer,
                    "attempted_at":  a.attempted_at,
                }
                for a in body.attempts
            ],
        )
        db.commit()
        return {"ok": True, "count": len(body.attempts)}
    except SQLAlchemyError as e:
        db.rollback()
        logger.error("save_word_attempts_batch failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to save word attempts")
