"""
services/streak_engine.py — Streak tracking and calculation
Section: System
Dependencies: models.py (StreakLog, DayOffRequest, AppConfig, WordReview)
API: called by routers/xp.py, routers/arcade.py, routers/*math*.py
"""

from datetime import date, timedelta
from sqlalchemy.orm import Session
from backend.models import StreakLog, DayOffRequest, WordReview, AppConfig


# ─── Config helpers ───────────────────────────────────────────

_VALID_SUBJECTS = {"english", "math", "game"}
_DEFAULT_SUBJECTS = {"english", "math", "game"}
_DEFAULT_MODE = "all"


# @tag STREAK
def get_streak_config(db: Session) -> tuple[set[str], str]:
    """Return (subjects, mode) from AppConfig with safe defaults.

    subjects: set of {"english","math","game"} that count toward streak.
    mode: "all" (every selected subject required) or "any" (at least one).
    """
    sub_row = db.query(AppConfig).filter(AppConfig.key == "streak_subjects").first()
    mode_row = db.query(AppConfig).filter(AppConfig.key == "streak_mode").first()
    raw = (sub_row.value if sub_row else "") or ""
    subjects = {s.strip() for s in raw.split(",") if s.strip() in _VALID_SUBJECTS}
    if not subjects:
        subjects = set(_DEFAULT_SUBJECTS)
    mode = (mode_row.value if mode_row else "") or _DEFAULT_MODE
    if mode not in ("all", "any"):
        mode = _DEFAULT_MODE
    return subjects, mode


# ─── Log access ───────────────────────────────────────────────

# @tag STREAK
def get_or_create_streak_log(db: Session, day: str | None = None) -> StreakLog:
    """Get or create a StreakLog for the given date (defaults to today)."""
    day = day or date.today().isoformat()
    log = db.query(StreakLog).filter(StreakLog.date == day).first()
    if not log:
        log = StreakLog(
            date=day,
            review_done=False,
            daily_words_done=False,
            math_done=False,
            game_done=False,
            streak_maintained=False,
        )
        db.add(log)
        db.commit()
        db.refresh(log)
    return log


# ─── Mark activity ────────────────────────────────────────────

# @tag STREAK
def mark_review_done(db: Session, day: str | None = None) -> None:
    """Mark review as done and re-evaluate streak. @tag ENGLISH"""
    log = get_or_create_streak_log(db, day)
    log.review_done = True
    db.commit()
    _evaluate_streak(db, log)


# @tag STREAK
def mark_daily_words_done(db: Session, day: str | None = None) -> None:
    """Mark daily words as done and re-evaluate streak. @tag ENGLISH"""
    log = get_or_create_streak_log(db, day)
    log.daily_words_done = True
    db.commit()
    _evaluate_streak(db, log)


# @tag STREAK @tag MATH
def mark_math_done(db: Session, day: str | None = None) -> None:
    """Mark math activity as done and re-evaluate streak.

    Called from any meaningful math completion (academy unit test pass,
    daily challenge finish, fact fluency round, kangaroo set complete).
    """
    log = get_or_create_streak_log(db, day)
    if not log.math_done:
        log.math_done = True
        db.commit()
    _evaluate_streak(db, log)


# @tag STREAK @tag ARCADE
def mark_game_done(db: Session, day: str | None = None) -> None:
    """Mark arcade/game activity as done and re-evaluate streak."""
    log = get_or_create_streak_log(db, day)
    if not log.game_done:
        log.game_done = True
        db.commit()
    _evaluate_streak(db, log)


# ─── Subject evaluation ───────────────────────────────────────

# @tag STREAK
def _reviews_were_due(db: Session, day: str) -> bool:
    """True if any SM-2 review was scheduled on or before the given day."""
    try:
        return (
            db.query(WordReview)
              .filter(WordReview.next_review_date != None)  # noqa: E711
              .filter(WordReview.next_review_date <= day)
              .first()
            is not None
        )
    except Exception:
        return True


# @tag STREAK @tag ENGLISH
def _english_ok(db: Session, log: StreakLog) -> bool:
    """English subject requirement: review+daily_words (or daily_words alone when no reviews were due)."""
    if log.review_done and log.daily_words_done:
        return True
    if log.daily_words_done and not _reviews_were_due(db, log.date):
        return True
    return False


# @tag STREAK
def _evaluate_streak(db: Session, log: StreakLog) -> None:
    """Determine if streak is maintained for log's date, honoring AppConfig rule.

    Rules:
    - Approved Day Off → maintained (freeze)
    - Otherwise: per-subject flags evaluated against (subjects, mode) config.
      mode="all": every configured subject must be satisfied.
      mode="any": at least one configured subject must be satisfied.
    """
    day_off = db.query(DayOffRequest).filter(
        DayOffRequest.request_date == log.date,
        DayOffRequest.status == "approved",
    ).first()
    if day_off:
        log.streak_maintained = True
        db.commit()
        return

    subjects, mode = get_streak_config(db)
    flags = {
        "english": _english_ok(db, log),
        "math":    bool(log.math_done),
        "game":    bool(log.game_done),
    }
    required = [flags[s] for s in subjects]
    if not required:
        log.streak_maintained = False
    elif mode == "any":
        log.streak_maintained = any(required)
    else:
        log.streak_maintained = all(required)
    db.commit()


# @tag STREAK
def re_evaluate_range(db: Session, days: int = 7) -> int:
    """Re-run _evaluate_streak for the last N days (inclusive of today).

    Used when the parent changes the streak rule and wants retroactive recalc.
    Returns the number of logs re-evaluated.
    """
    today = date.today()
    count = 0
    for i in range(max(1, days)):
        d = (today - timedelta(days=i)).isoformat()
        log = db.query(StreakLog).filter(StreakLog.date == d).first()
        if log:
            _evaluate_streak(db, log)
            count += 1
    return count


# ─── Read-side helpers ────────────────────────────────────────

# @tag STREAK
def get_current_streak(db: Session) -> int:
    """Consecutive maintained days ending today-or-yesterday (max 365 lookback)."""
    streak = 0
    check_date = date.today()
    for _ in range(365):
        day_str = check_date.isoformat()
        log = db.query(StreakLog).filter(StreakLog.date == day_str).first()
        if log and log.streak_maintained:
            streak += 1
            check_date -= timedelta(days=1)
        elif check_date == date.today():
            check_date -= timedelta(days=1)
        else:
            break
    return streak


# @tag STREAK
def check_streak_bonus(
    db: Session,
    current_streak: int,
    action_prefix: str = "",
) -> str | None:
    """7-day/30-day milestone bonus action key, or None."""
    if current_streak > 0 and current_streak % 30 == 0:
        return "streak_30_bonus"
    if current_streak > 0 and current_streak % 7 == 0:
        return "streak_7_bonus"
    return None
