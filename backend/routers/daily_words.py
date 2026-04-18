"""
routers/daily_words.py — Daily Words 7-day cycle API
Section: English / Daily Words
Dependencies: services/daily_words_engine.py, services/xp_engine.py, services/streak_engine.py
API: GET /api/daily-words/status, GET /api/daily-words/today,
     POST /api/daily-words/day1-result, POST /api/daily-words/complete,
     GET /api/daily-words/weekly-test, POST /api/daily-words/weekly-test/result
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

try:
    from ..database import get_db
    from ..services import daily_words_engine as dwe
    from ..services import xp_engine, streak_engine
    from ..models import WordReview
except ImportError:
    from database import get_db
    from services import daily_words_engine as dwe
    from services import xp_engine, streak_engine
    from models import WordReview

from datetime import date as _date, timedelta

router = APIRouter()
logger = logging.getLogger(__name__)


# @tag DAILY_WORDS @tag REVIEW @tag SM2
def _register_daily_words_for_review(db: Session, today_payload: dict) -> None:
    """Insert today's Daily Words into WordReview so they appear in unified Review.

    De-duplicates by (source='daily', source_ref=grade/day, word). Day 1 and
    Day 7 are tests — skip registration on those days.
    """
    cycle_day = today_payload.get("cycle_day", 0)
    if cycle_day in (1, 7):
        return
    grade = today_payload.get("grade", "")
    words = today_payload.get("words", []) or []
    if not words:
        return
    source_ref = f"{grade}/day_{cycle_day}"
    tomorrow = (_date.today() + timedelta(days=1)).isoformat()
    word_strs = [w.get("word", "") for w in words if w.get("word")]
    existing = {
        row.word for row in
        db.query(WordReview.word)
        .filter(
            WordReview.source == "daily",
            WordReview.source_ref == source_ref,
            WordReview.word.in_(word_strs),
        ).all()
    }
    for w in words:
        name = w.get("word", "")
        if not name or name in existing:
            continue
        db.add(WordReview(
            study_item_id=None, word=name,
            subject="English", textbook="", lesson="",
            easiness="2.5", interval=0, repetitions=0,
            next_review=tomorrow, last_review="",
            total_reviews=0, total_correct=0,
            source="daily",
            question=w.get("definition", "") or "",
            hint=w.get("example", "") or "",
            source_ref=source_ref,
        ))
    db.commit()


# ─── Pydantic schemas ─────────────────────────────────────────

class Day1ResultIn(BaseModel):
    failed_words: list[str]


class DailyCompleteIn(BaseModel):
    learned_count: int = dwe.DAILY_TARGET


class WeeklyTestResultIn(BaseModel):
    correct_count: int
    total_count: int
    advance_grade: bool = False


# ─── Endpoints ────────────────────────────────────────────────

@router.get("/api/daily-words/status")
def daily_words_status(db: Session = Depends(get_db)):
    """
    Return sidebar summary: grade, week progress, today progress.
    @tag DAILY_WORDS
    """
    try:
        return dwe.get_status(db)
    except Exception as exc:
        logger.error("daily_words_status error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/api/daily-words/today")
def daily_words_today(db: Session = Depends(get_db)):
    """
    Return words and metadata for today's session.
    @tag DAILY_WORDS
    """
    try:
        return dwe.get_today_words(db)
    except Exception as exc:
        logger.error("daily_words_today error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/api/daily-words/day1-result")
def daily_words_day1_result(body: Day1ResultIn, db: Session = Depends(get_db)):
    """
    Record Day 1 placement test results (list of words the student got wrong).
    These become the study set for Days 2–6.
    @tag DAILY_WORDS
    """
    try:
        dwe.record_day1_failures(db, body.failed_words)
        return {"ok": True, "failed_count": len(body.failed_words)}
    except Exception as exc:
        logger.error("daily_words_day1_result error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/api/daily-words/complete")
def daily_words_complete(body: DailyCompleteIn, db: Session = Depends(get_db)):
    """
    Mark today's daily study as complete.
    Awards XP +5 and marks daily_words_done on StreakLog.
    @tag DAILY_WORDS XP STREAK
    """
    try:
        today_payload = dwe.get_today_words(db)
        dwe.mark_daily_complete(db, body.learned_count)

        # Register today's studied words into the unified SM-2 Review queue.
        _register_daily_words_for_review(db, today_payload)

        # Award XP
        xp_awarded = xp_engine.award_xp(db, "daily_words_complete", "daily_words")

        # Mark streak
        streak_engine.mark_daily_words_done(db)

        return {"ok": True, "xp_awarded": xp_awarded}
    except Exception as exc:
        logger.error("daily_words_complete error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/api/daily-words/weekly-test")
def daily_words_weekly_test(db: Session = Depends(get_db)):
    """
    Return the weekly test word set (Day 7).
    @tag DAILY_WORDS
    """
    try:
        data = dwe.get_today_words(db)
        if data["cycle_day"] != 7:
            raise HTTPException(status_code=400, detail="Weekly test only available on Day 7")
        return data
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("daily_words_weekly_test error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/api/daily-words/weekly-test/result")
def daily_words_weekly_test_result(body: WeeklyTestResultIn, db: Session = Depends(get_db)):
    """
    Record weekly test result.
    Pass (≥90%) → award XP +10, advance cycle (optionally advance grade).
    Fail → advance cycle at same grade.
    @tag DAILY_WORDS XP STREAK
    """
    try:
        accuracy = body.correct_count / max(body.total_count, 1)
        passed = accuracy >= dwe.WEEKLY_PASS_PCT
        xp_awarded = 0

        if passed:
            xp_awarded = xp_engine.award_xp(db, "weekly_test_pass", "daily_words")

        # Advance cycle (grade may advance based on accuracy or explicit flag)
        adjustment = dwe.check_grade_adjustment(db, accuracy)
        should_advance_grade = body.advance_grade or (adjustment == "advance")
        new_grade = dwe.advance_cycle(db) if should_advance_grade else _advance_cycle_same_grade(db)

        # Mark daily words done for streak
        streak_engine.mark_daily_words_done(db)

        return {
            "ok": True,
            "passed": passed,
            "accuracy": round(accuracy, 3),
            "xp_awarded": xp_awarded,
            "new_grade": new_grade,
            "grade_advanced": should_advance_grade,
        }
    except Exception as exc:
        logger.error("daily_words_weekly_test_result error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


# ─── Private helpers ──────────────────────────────────────────

def _advance_cycle_same_grade(db: Session) -> str:
    """
    Start a new cycle at the same grade (used when grade doesn't advance).
    @tag DAILY_WORDS SYSTEM
    """
    from datetime import date
    try:
        from ..models import DailyWordsProgress
    except ImportError:
        from models import DailyWordsProgress
    import json

    prog = db.query(DailyWordsProgress).first()
    if prog is None:
        return "grade_3"
    today_str = date.today().isoformat()
    prog.cycle_start = today_str
    prog.word_index = 0
    prog.test_words_json = "[]"
    prog.daily_learned = 0
    prog.last_study_date = None
    db.commit()
    return prog.grade
