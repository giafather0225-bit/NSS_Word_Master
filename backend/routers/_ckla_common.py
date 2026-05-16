"""
_ckla_common.py — Shared constants, schemas, and helpers for CKLA router modules.
Section: Academy
Dependencies: models/ckla, models/us_academy, database
API endpoints: none (imported by ckla.py, ckla_progress.py, ckla_domain_test.py, ckla_grade_test.py)
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.models.ckla import CKLALesson, CKLALessonProgress, CKLABadge
from backend.models.us_academy import USAcademyWord

NOW = lambda: datetime.now().isoformat(timespec="seconds")

# AppConfig key constants
_CFG_DOMAIN_ORDER_FIXED = "ckla_domain_order_fixed"
_CFG_DAILY_GOAL         = "ckla_daily_goal"
_CFG_DOMAIN_PASS_PCT    = "ckla_domain_pass_pct"
_CFG_GRADE_PASS_PCT     = "ckla_grade_pass_pct"

_SUPPORTED_GRADES = [3]
_GRADE_TITLES = {3: "Grade 3"}

_RANK_THRESHOLDS = [
    (100, "Master"),
    (76,  "Champion"),
    (51,  "Adventurer"),
    (26,  "Explorer"),
    (0,   "Beginner"),
]


# ── Pydantic Schemas ──────────────────────────────────────────────────────────

class ProgressUpdate(BaseModel):
    reading_done:     Optional[bool] = None
    vocab_done:       Optional[bool] = None
    qa_done:          Optional[bool] = None
    word_work_done:   Optional[bool] = None
    word_work_answer: Optional[str] = Field(default=None, max_length=2000)


class AnswerSubmit(BaseModel):
    user_answer: str = Field(max_length=2000)


class DifficultyRating(BaseModel):
    rating: str = Field(..., pattern="^(easy|neutral|hard)$")


class DomainTestSubmit(BaseModel):
    answers: dict[int, str]
    time_taken_seconds: Optional[int] = None


class GradeFinalTestSubmit(BaseModel):
    answers: dict[int, str]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _grade_rank(completion_pct: float) -> str:
    for threshold, rank in _RANK_THRESHOLDS:
        if completion_pct >= threshold:
            return rank
    return "Beginner"


def _get_or_create_progress(db: Session, lesson_id: int) -> CKLALessonProgress:
    prog = db.query(CKLALessonProgress).filter_by(lesson_id=lesson_id).first()
    if not prog:
        lesson = db.query(CKLALesson).filter_by(id=lesson_id).first()
        try:
            prog = CKLALessonProgress(
                lesson_id=lesson_id,
                grade=lesson.grade if lesson else 3,
                started_at=NOW(),
            )
            db.add(prog)
            db.flush()
        except IntegrityError:
            db.rollback()
            prog = db.query(CKLALessonProgress).filter_by(lesson_id=lesson_id).first()
    return prog


def _progress_dict(p: Optional[CKLALessonProgress]) -> dict:
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


def _word_dict(w: USAcademyWord) -> dict:
    import json
    return {
        "id":             w.id,
        "word":           w.word,
        "definition":     w.definition or "",
        "part_of_speech": w.part_of_speech or "",
        "audio_url":      w.audio_url or "",
        "example_1":      w.example_1 or "",
        "all_defs":       json.loads(w.synonyms_json or "[]"),
    }


def _badge_dict(b: CKLABadge, earned_at: Optional[str] = None) -> dict:
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
