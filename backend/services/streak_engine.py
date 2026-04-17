"""
services/streak_engine.py — Streak tracking and calculation
Section: System
Dependencies: models.py (StreakLog, DayOffRequest)
API: called by routers/xp.py
"""

from datetime import date, timedelta, datetime
from sqlalchemy.orm import Session
from backend.models import StreakLog, DayOffRequest, WordReview


# @tag STREAK
def get_or_create_streak_log(db: Session, day: str | None = None) -> StreakLog:
    """Get or create a StreakLog for the given date (defaults to today).

    Args:
        db: SQLAlchemy session.
        day: ISO date string (YYYY-MM-DD); defaults to today.

    Returns:
        Existing or newly created StreakLog row.
    """
    day = day or date.today().isoformat()
    log = db.query(StreakLog).filter(StreakLog.date == day).first()
    if not log:
        log = StreakLog(
            date=day,
            review_done=False,
            daily_words_done=False,
            streak_maintained=False,
        )
        db.add(log)
        db.commit()
        db.refresh(log)
    return log


# @tag STREAK
def mark_review_done(db: Session, day: str | None = None) -> None:
    """Mark review as done for the given date and re-evaluate streak.

    Args:
        db: SQLAlchemy session.
        day: ISO date string override; defaults to today.
    """
    log = get_or_create_streak_log(db, day)
    log.review_done = True
    db.commit()
    _evaluate_streak(db, log)


# @tag STREAK
def mark_daily_words_done(db: Session, day: str | None = None) -> None:
    """Mark daily words as done for the given date and re-evaluate streak.

    Args:
        db: SQLAlchemy session.
        day: ISO date string override; defaults to today.
    """
    log = get_or_create_streak_log(db, day)
    log.daily_words_done = True
    db.commit()
    _evaluate_streak(db, log)


# @tag STREAK
def _reviews_were_due(db: Session, day: str) -> bool:
    """Return True if any SM-2 review was scheduled on or before the given day.

    A "review-due day" is one where the student had at least one word whose
    next_review_date had already arrived. On a no-review day, completing
    daily_words alone is enough to maintain the streak (per CLAUDE.md spec).

    Args:
        db: SQLAlchemy session.
        day: ISO date string (YYYY-MM-DD) to check.
    """
    try:
        return (
            db.query(WordReview)
              .filter(WordReview.next_review_date != None)  # noqa: E711
              .filter(WordReview.next_review_date <= day)
              .first()
            is not None
        )
    except Exception:
        # If the column or table is missing for any reason, fail-open and
        # treat the day as having reviews due (preserves prior strict behavior).
        return True


# @tag STREAK
def _evaluate_streak(db: Session, log: StreakLog) -> None:
    """Determine if streak is maintained for log's date.

    Rules (per CLAUDE.md "Streak Rules"):
    - Approved Day Off → maintained (freeze)
    - Review-due day:  review_done AND daily_words_done → maintained
    - No-review day:   daily_words_done alone → maintained

    Args:
        db: SQLAlchemy session.
        log: The StreakLog row for the day being evaluated.
    """
    # 1. Approved day off freezes the streak regardless of activity
    day_off = db.query(DayOffRequest).filter(
        DayOffRequest.request_date == log.date,
        DayOffRequest.status == "approved",
    ).first()
    if day_off:
        log.streak_maintained = True
        db.commit()
        return

    # 2. Both review and daily words done → always maintained
    if log.review_done and log.daily_words_done:
        log.streak_maintained = True
        db.commit()
        return

    # 3. No-review day: daily_words alone suffices when no reviews were due.
    #    This was previously missing — students lost streaks on review-free
    #    days even though they completed daily words.
    if log.daily_words_done and not _reviews_were_due(db, log.date):
        log.streak_maintained = True
        db.commit()
        return

    # Otherwise: streak NOT maintained for this day. Leave streak_maintained=False.


# @tag STREAK
def get_current_streak(db: Session) -> int:
    """Count consecutive days (ending today or yesterday) where streak_maintained=True.

    Returns 0 if today is not yet maintained and no prior streak exists.
    Looks back up to 365 days to find the streak length.

    Args:
        db: SQLAlchemy session.

    Returns:
        Number of consecutive maintained days.
    """
    streak = 0
    check_date = date.today()

    for _ in range(365):  # max 1 year lookback
        day_str = check_date.isoformat()
        log = db.query(StreakLog).filter(StreakLog.date == day_str).first()

        if log and log.streak_maintained:
            streak += 1
            check_date -= timedelta(days=1)
        elif check_date == date.today():
            # Today not yet maintained — look back to yesterday to get current streak
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
    """Check if a streak milestone bonus should be awarded.

    Milestones: every 7 days → streak_7_bonus; every 30 days → streak_30_bonus.
    The 30-day check takes priority.

    Args:
        db: SQLAlchemy session (reserved for future use).
        current_streak: Current streak length in days.
        action_prefix: Unused; reserved for namespacing.

    Returns:
        Action key string if a bonus applies, otherwise None.
    """
    if current_streak > 0 and current_streak % 30 == 0:
        return "streak_30_bonus"
    if current_streak > 0 and current_streak % 7 == 0:
        return "streak_7_bonus"
    return None
