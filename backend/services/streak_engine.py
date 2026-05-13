"""
services/streak_engine.py — Streak tracking and calculation
Section: System
Dependencies: models.py (StreakLog, DayOffRequest, AppConfig, WordReview)
API: called by routers/xp.py, routers/arcade.py, routers/*math*.py
"""

import logging
from datetime import date, timedelta
from sqlalchemy.orm import Session
from backend.models import StreakLog, DayOffRequest, WordReview, AppConfig

logger = logging.getLogger(__name__)


# ─── Config helpers ───────────────────────────────────────────

_VALID_SUBJECTS = {"ckla", "english", "math", "game"}
_DEFAULT_SUBJECTS = {"ckla", "math", "game"}
_DEFAULT_MODE = "all"


# @tag STREAK
def get_streak_config(db: Session) -> tuple[set[str], str]:
    """Return (subjects, mode) from AppConfig with safe defaults.

    subjects: set of {"ckla","english","math","game"} that count toward streak.
    mode: "all" (every selected subject required) or "any" (at least one).
    """
    sub_row = db.query(AppConfig).filter(AppConfig.key == "streak_subjects").first()
    mode_row = db.query(AppConfig).filter(AppConfig.key == "streak_mode").first()
    raw = (sub_row.value if sub_row else "") or ""
    subjects = {s.strip() for s in raw.split(",") if s.strip() in _VALID_SUBJECTS}
    if not subjects:
        if raw.strip():
            logger.warning("streak_subjects config %r has no valid subjects; using defaults", raw)
        subjects = set(_DEFAULT_SUBJECTS)
    mode = (mode_row.value if mode_row else "") or _DEFAULT_MODE
    if mode not in ("all", "any"):
        logger.warning("streak_mode config %r is invalid; using default %r", mode, _DEFAULT_MODE)
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
            ckla_done=False,
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


# @tag STREAK @tag CKLA
def mark_ckla_done(db: Session, day: str | None = None, commit: bool = True) -> None:
    """Mark CKLA lesson completed for the day and re-evaluate streak.

    Args:
        commit: If False, only db.add() mutations — caller is responsible for
                db.commit(). Pass commit=False when called inside a larger
                transaction (e.g. update_lesson_progress) to keep all writes
                atomic.
    """
    log = get_or_create_streak_log(db, day)
    if not log.ckla_done:
        log.ckla_done = True
        if commit:
            db.commit()
    _evaluate_streak(db, log, commit=commit)


# ─── Island lumi for streak ───────────────────────────────────

def _award_streak_lumi(db: Session) -> None:
    """Award Lumi when today's streak is first confirmed maintained. Silent on any error."""
    try:
        cfg = db.query(AppConfig).filter_by(key="lumi_rule_streak").first()
        try:
            amount = max(0, int(cfg.value)) if cfg else 5
        except (TypeError, ValueError):
            amount = 5
        if amount <= 0:
            return
        from backend.services.lumi_engine import earn_lumi
        earn_lumi(db, source="streak", amount=amount)
    except Exception:
        pass


# ─── Subject evaluation ───────────────────────────────────────

# @tag STREAK
def _reviews_were_due(db: Session, day: str) -> bool:
    """True if any SM-2 review was scheduled on or before the given day."""
    return (
        db.query(WordReview)
          .filter(WordReview.next_review != None)  # noqa: E711
          .filter(WordReview.next_review <= day)
          .first()
        is not None
    )


# @tag STREAK @tag ENGLISH
def _english_ok(db: Session, log: StreakLog) -> bool:
    """English subject requirement: review+daily_words (or daily_words alone when no reviews due)."""
    if log is None:
        return False
    if log.review_done and log.daily_words_done:
        return True
    if log.daily_words_done and not _reviews_were_due(db, log.date):
        return True
    return False


# @tag STREAK @tag CKLA
def _ckla_ok(db: Session, log: StreakLog) -> bool:
    """CKLA subject requirement: at least one lesson completed today (via ckla_done flag)."""
    return bool(log.ckla_done)


# @tag STREAK
def _evaluate_streak(db: Session, log: StreakLog, commit: bool = True) -> None:
    """Determine if streak is maintained for log's date, honoring AppConfig rule.

    Rules:
    - Approved Day Off → maintained (freeze)
    - Otherwise: per-subject flags evaluated against (subjects, mode) config.
      mode="all": every configured subject must be satisfied.
      mode="any": at least one configured subject must be satisfied.

    Both branches share a single db.commit() at the end so the Day-Off case
    and the normal evaluation case are each one atomic write.

    Args:
        commit: If False, skip db.commit() and lumi side-effects — caller is
                responsible for committing the session atomically. Lumi award
                is omitted in this path to avoid a premature inner commit.
    """
    was_maintained = bool(log.streak_maintained)
    today_str = date.today().isoformat()

    day_off = db.query(DayOffRequest).filter(
        DayOffRequest.request_date == log.date,
        DayOffRequest.status == "approved",
    ).first()
    if day_off:
        log.streak_maintained = True
    else:
        subjects, mode = get_streak_config(db)
        flags = {
            "ckla":    _ckla_ok(db, log),
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

    if commit:
        db.commit()
        if not was_maintained and log.streak_maintained and log.date == today_str:
            _award_streak_lumi(db)


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
    """Consecutive maintained days ending today-or-yesterday (max 365 lookback).

    Batch-loads up to 365 StreakLog rows ordered DESC (1 query) instead of
    issuing one query per day (N+1 pattern).
    """
    today = date.today()
    cutoff = (today - timedelta(days=364)).isoformat()
    rows = (
        db.query(StreakLog)
        .filter(StreakLog.date >= cutoff)
        .order_by(StreakLog.date.desc())
        .all()
    )
    maintained_days: set[str] = {r.date for r in rows if r.streak_maintained}

    streak = 0
    check_date = today
    for _ in range(365):
        day_str = check_date.isoformat()
        if day_str in maintained_days:
            streak += 1
            check_date -= timedelta(days=1)
        elif check_date == today:
            # Today not yet maintained — check yesterday
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
