"""
services/xp_engine.py — XP calculation and award logic
Section: System
Dependencies: models.py (XPLog, WordReview)
API: called by routers/xp.py
"""

from datetime import datetime, date
from sqlalchemy.orm import Session
from models import XPLog, WordReview

# XP awarded per action (immutable)
XP_RULES: dict[str, int] = {
    "word_correct":           1,
    "stage_complete":         2,
    "final_test_pass":       10,
    "unit_test_pass":         5,
    "daily_words_complete":   5,
    "weekly_test_pass":      10,
    "review_complete":        2,
    "journal_complete":      10,
    "must_do_bonus":          5,
    "all_complete_bonus":    15,
    "streak_7_bonus":        30,
    "streak_30_bonus":       200,
}


# @tag XP @tag AWARD
def award_xp(
    db: Session,
    action: str,
    detail: str = "",
    earned_date: str | None = None,
) -> int:
    """Award XP for an action. Returns actual XP awarded (0 if already awarded today).

    Daily dedup: same action + same earned_date = skip.
    For word_correct, detail should be the word string (allows multiple per day).

    Args:
        db: SQLAlchemy session.
        action: Key from XP_RULES (e.g. "stage_complete").
        detail: Optional extra context (word string for word_correct).
        earned_date: ISO date string override; defaults to today.

    Returns:
        XP points actually inserted, or 0 if deduped / unknown action.
    """
    today = earned_date or date.today().isoformat()
    xp_amount = XP_RULES.get(action, 0)
    if xp_amount == 0:
        return 0

    # Dedup check (skip for word_correct — multiple per day is fine)
    if action != "word_correct":
        existing = db.query(XPLog).filter(
            XPLog.action == action,
            XPLog.earned_date == today,
        ).first()
        if existing:
            return 0

    log = XPLog(
        action=action,
        xp_amount=xp_amount,
        detail=detail,
        earned_date=today,
        created_at=datetime.now().isoformat(),
    )
    db.add(log)
    db.commit()
    return xp_amount


# @tag XP
def get_total_xp(db: Session) -> int:
    """Return sum of all XP ever earned.

    Args:
        db: SQLAlchemy session.

    Returns:
        Total XP as an integer (0 if no records).
    """
    from sqlalchemy import func
    result = db.query(func.sum(XPLog.xp_amount)).scalar()
    return int(result or 0)


# @tag XP
def get_today_xp(db: Session) -> int:
    """Return sum of XP earned today.

    Args:
        db: SQLAlchemy session.

    Returns:
        Today's XP total as an integer (0 if no records).
    """
    from sqlalchemy import func
    today = date.today().isoformat()
    result = (
        db.query(func.sum(XPLog.xp_amount))
        .filter(XPLog.earned_date == today)
        .scalar()
    )
    return int(result or 0)


# @tag XP @tag SHOP
def spend_xp(db: Session, amount: int, detail: str = "") -> bool:
    """Deduct XP for a shop purchase. Returns False if insufficient balance.

    Args:
        db: SQLAlchemy session.
        amount: XP to deduct (positive number).
        detail: Purchase description.

    Returns:
        True if deduction succeeded, False if not enough XP.
    """
    if get_total_xp(db) < amount:
        return False
    log = XPLog(
        action="shop_purchase",
        xp_amount=-amount,
        detail=detail,
        earned_date=date.today().isoformat(),
        created_at=datetime.now().isoformat(),
    )
    db.add(log)
    db.commit()
    return True


# @tag XP
def get_words_known(db: Session) -> int:
    """Return count of WordReview entries with interval >= 7 (mastered words).

    Args:
        db: SQLAlchemy session.

    Returns:
        Number of words with SM-2 interval >= 7 days.
    """
    return db.query(WordReview).filter(WordReview.interval >= 7).count()
