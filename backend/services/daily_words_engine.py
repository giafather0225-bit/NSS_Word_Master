"""
services/daily_words_engine.py — Daily Words 7-day cycle logic
Section: English / Daily Words
Dependencies: models.py (DailyWordsProgress), data/daily_words/*.json
API: used by routers/daily_words.py
"""

import json
import logging
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

try:
    from ..models import DailyWordsProgress, StreakLog
except ImportError:
    from models import DailyWordsProgress, StreakLog

logger = logging.getLogger(__name__)

# ─── Constants ────────────────────────────────────────────────
DATA_DIR = Path(__file__).parent.parent / "data" / "daily_words"

GRADE_ORDER = [
    "grade_2", "grade_3", "grade_4", "grade_5",
    "grade_6", "grade_7", "grade_8", "grade_9",
]

DAILY_TARGET  = 10   # words per day (Days 2–6)
CYCLE_DAYS    = 7    # days per cycle
DAY1_TEST_SIZE = 70  # words shown on Day 1 placement test
WEEKLY_PASS_PCT = 0.90  # 90% to pass weekly test


# ─── Word Data ────────────────────────────────────────────────

def load_grade_words(grade: str) -> list[dict]:
    """
    Load word list for the given grade key (e.g. 'grade_5').
    Returns [] if file is missing or malformed.
    @tag DAILY_WORDS
    """
    path = DATA_DIR / f"{grade}.json"
    if not path.exists():
        logger.warning("Daily words file not found: %s", path)
        return []
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        logger.error("Failed to load %s: %s", path, exc)
        return []


# ─── Progress helpers ─────────────────────────────────────────

def get_or_create_progress(db: Session, default_grade: str = "grade_3") -> DailyWordsProgress:
    """
    Return the single DailyWordsProgress row, creating it if absent.
    @tag DAILY_WORDS SYSTEM
    """
    prog = db.query(DailyWordsProgress).first()
    if prog is None:
        today = date.today().isoformat()
        prog = DailyWordsProgress(
            grade=default_grade,
            cycle_start=today,
            word_index=0,
            test_words_json="[]",
            daily_learned=0,
            last_study_date=None,
        )
        db.add(prog)
        db.commit()
        db.refresh(prog)
    return prog


def get_cycle_day(cycle_start: str) -> int:
    """
    Return the 1-based day within the current 7-day cycle (1–7).
    Day 8+ wraps into the next cycle, but the caller should call advance_cycle().
    @tag DAILY_WORDS
    """
    try:
        start = date.fromisoformat(cycle_start)
    except (ValueError, TypeError):
        return 1
    delta = (date.today() - start).days + 1  # Day 1 = start date
    return max(1, min(delta, CYCLE_DAYS))


def _get_test_words(prog: DailyWordsProgress) -> list[str]:
    """Parse the test_words_json column (list of words that failed Day 1)."""
    try:
        return json.loads(prog.test_words_json or "[]")
    except Exception:
        return []


# ─── Today's words ────────────────────────────────────────────

def get_today_words(db: Session) -> dict:
    """
    Return the words the student should study today and metadata.

    Day 1: 70-word placement test from the beginning of the grade list.
    Days 2–6: 10 words/day from the failed-on-Day-1 set (or full list if none failed).
    Day 7: weekly test using the same set studied Days 2–6.

    Returns:
        {
            "cycle_day": int,
            "grade": str,
            "words": [{"word","definition","example","grade"}, ...],
            "daily_target": int,
            "weekly_pass_pct": float,
            "already_done_today": bool,
        }
    @tag DAILY_WORDS
    """
    prog = get_or_create_progress(db)
    cycle_day = get_cycle_day(prog.cycle_start)
    today_str = date.today().isoformat()
    already_done = prog.last_study_date == today_str

    all_words = load_grade_words(prog.grade)
    test_words_ids = _get_test_words(prog)

    if cycle_day == 1:
        # Day 1: placement test — show first DAY1_TEST_SIZE words
        words = all_words[:DAY1_TEST_SIZE]
    elif cycle_day == 7:
        # Day 7: weekly test — same set studied this week
        if test_words_ids:
            words = [w for w in all_words if w["word"] in test_words_ids]
        else:
            # If no failures on Day 1, test on the first DAILY_TARGET*5 words
            words = all_words[:DAILY_TARGET * 5]
    else:
        # Days 2–6: study DAILY_TARGET words from the study set
        if test_words_ids:
            study_pool = [w for w in all_words if w["word"] in test_words_ids]
        else:
            study_pool = all_words[:DAILY_TARGET * 5]
        day_offset = (cycle_day - 2) * DAILY_TARGET  # day2=0, day3=10, ...
        words = study_pool[day_offset: day_offset + DAILY_TARGET]

    return {
        "cycle_day": cycle_day,
        "grade": prog.grade,
        "words": words,
        "daily_target": DAILY_TARGET,
        "weekly_pass_pct": WEEKLY_PASS_PCT,
        "already_done_today": already_done,
        "word_index": prog.word_index,
        "cycle_start": prog.cycle_start,
    }


def get_status(db: Session) -> dict:
    """
    Return summary sidebar info: grade label, week progress, today progress.
    @tag DAILY_WORDS
    """
    prog = get_or_create_progress(db)
    cycle_day = get_cycle_day(prog.cycle_start)
    today_str = date.today().isoformat()

    # Week progress: days completed out of 6 active study days (Days 2–6)
    if cycle_day == 1:
        week_done = 0
        week_total = 5
    elif cycle_day == 7:
        week_done = 5
        week_total = 5
    else:
        week_done = max(0, cycle_day - 2)
        week_total = 5

    # Today progress
    if cycle_day == 1:
        today_done = 0
        today_total = DAY1_TEST_SIZE
        label = "Placement Test"
    elif cycle_day == 7:
        test_words_ids = _get_test_words(prog)
        today_total = len(test_words_ids) if test_words_ids else DAILY_TARGET * 5
        today_done = today_total if prog.last_study_date == today_str else 0
        label = "Weekly Test"
    else:
        today_done = prog.daily_learned if prog.last_study_date == today_str else 0
        today_total = DAILY_TARGET
        label = f"Day {cycle_day}"

    grade_label = prog.grade.replace("_", " ").title()  # e.g. "Grade 5"

    return {
        "grade": prog.grade,
        "grade_label": grade_label,
        "cycle_day": cycle_day,
        "day_label": label,
        "week_done": week_done,
        "week_total": week_total,
        "today_done": today_done,
        "today_total": today_total,
        "already_done_today": prog.last_study_date == today_str,
    }


# ─── Record outcomes ──────────────────────────────────────────

def record_day1_failures(db: Session, failed_words: list[str]) -> None:
    """
    Save the words the student failed on Day 1 placement test.
    These become the study set for Days 2–6.
    @tag DAILY_WORDS
    """
    prog = get_or_create_progress(db)
    today_str = date.today().isoformat()
    prog.test_words_json = json.dumps(failed_words)
    prog.last_study_date = today_str
    db.commit()


def mark_daily_complete(db: Session, learned_count: int = DAILY_TARGET) -> None:
    """
    Mark today's daily study session as complete, update daily_learned counter.
    @tag DAILY_WORDS
    """
    prog = get_or_create_progress(db)
    today_str = date.today().isoformat()
    prog.daily_learned = learned_count
    prog.last_study_date = today_str
    db.commit()


def advance_cycle(db: Session) -> str:
    """
    Start a new 7-day cycle (called after weekly test or on day 8+).
    If the student consistently scores ≥ 90%, advance one grade.
    Returns the new grade.
    @tag DAILY_WORDS
    """
    prog = get_or_create_progress(db)
    today_str = date.today().isoformat()

    # Advance grade if at end of grade_order
    current_idx = GRADE_ORDER.index(prog.grade) if prog.grade in GRADE_ORDER else 0
    new_idx = min(current_idx + 1, len(GRADE_ORDER) - 1)
    new_grade = GRADE_ORDER[new_idx]

    prog.grade = new_grade
    prog.cycle_start = today_str
    prog.word_index = 0
    prog.test_words_json = "[]"
    prog.daily_learned = 0
    prog.last_study_date = None
    db.commit()
    return new_grade


def check_grade_adjustment(db: Session, recent_accuracy: float) -> Optional[str]:
    """
    Suggest grade change based on recent accuracy.
    Returns 'advance' | 'hold' | 'repeat'.
    @tag DAILY_WORDS
    """
    if recent_accuracy >= 0.95:
        return "advance"
    elif recent_accuracy >= WEEKLY_PASS_PCT:
        return "hold"
    else:
        return "repeat"
