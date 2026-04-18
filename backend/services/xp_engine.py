"""
services/xp_engine.py — XP calculation and award logic
Section: System
Dependencies: models.py (XPLog, WordReview)
API: called by routers/xp.py
"""

from datetime import datetime, date
from sqlalchemy.orm import Session
from backend.models import XPLog, WordReview

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

# Arcade XP is variable per play (tier-based); awarded directly via award_arcade_xp
# rather than through XP_RULES. Daily cap is enforced in award_arcade_xp.
ARCADE_DAILY_CAP = 10


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


# @tag XP @tag ARCADE
def score_to_arcade_tier(score: int) -> int:
    """Map arcade score to XP tier (0/1/2/3)."""
    if score >= 2000:
        return 3
    if score >= 1000:
        return 2
    if score >= 500:
        return 1
    return 0


# @tag XP @tag ARCADE
def get_arcade_xp_today(db: Session) -> int:
    """Return total arcade XP earned today."""
    from sqlalchemy import func
    today = date.today().isoformat()
    result = (
        db.query(func.sum(XPLog.xp_amount))
        .filter(XPLog.action == "arcade_play", XPLog.earned_date == today)
        .scalar()
    )
    return int(result or 0)


# @tag XP @tag ARCADE
def award_arcade_xp(db: Session, score: int, game: str = "word_invaders") -> dict:
    """Award tier-based arcade XP, respecting ARCADE_DAILY_CAP.

    Tiers: 500+ = 1 XP, 1000+ = 2 XP, 2000+ = 3 XP. Partial awards allowed
    (e.g. if 2 XP remaining in cap and tier grants 3, award 2).

    Returns:
        {"tier": int, "xp_awarded": int, "daily_total": int, "daily_cap": int}
    """
    tier = score_to_arcade_tier(score)
    earned_today = get_arcade_xp_today(db)
    remaining = max(0, ARCADE_DAILY_CAP - earned_today)
    to_award = min(tier, remaining)

    if to_award > 0:
        log = XPLog(
            action="arcade_play",
            xp_amount=to_award,
            detail=f"{game}:score={score}:tier={tier}",
            earned_date=date.today().isoformat(),
            created_at=datetime.now().isoformat(),
        )
        db.add(log)
        db.commit()

    return {
        "tier": tier,
        "xp_awarded": to_award,
        "daily_total": earned_today + to_award,
        "daily_cap": ARCADE_DAILY_CAP,
    }


# @tag XP
def get_words_known(db: Session) -> int:
    """Return count of WordReview entries with interval >= 7 (mastered words).

    Args:
        db: SQLAlchemy session.

    Returns:
        Number of words with SM-2 interval >= 7 days.
    """
    return db.query(WordReview).filter(WordReview.interval >= 7).count()
