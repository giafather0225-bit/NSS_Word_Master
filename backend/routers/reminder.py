"""
routers/reminder.py — Home dashboard reminder banners
Section: Home
Dependencies: models.py (StreakLog, WordReview, AcademySession, GrowthEvent, DayOffRequest)
API: GET /api/reminders/today
"""

from datetime import date, datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

try:
    from ..database import get_db
    from ..models import (
        StreakLog, WordReview, AcademySession, GrowthEvent, DayOffRequest,
    )
except ImportError:
    from database import get_db  # type: ignore
    from models import (  # type: ignore
        StreakLog, WordReview, AcademySession, GrowthEvent, DayOffRequest,
    )

router = APIRouter(prefix="/api/reminders", tags=["reminders"])


# @tag REMINDER HOME_DASHBOARD
def _review_due_count(db: Session, today_iso: str) -> int:
    """Return the number of words whose SM-2 next_review_date is on or before today."""
    try:
        return (
            db.query(WordReview)
              .filter(WordReview.next_review_date != None)  # noqa: E711
              .filter(WordReview.next_review_date <= today_iso)
              .count()
        )
    except Exception:
        return 0


# @tag REMINDER HOME_DASHBOARD
def _streak_at_risk(db: Session, today_iso: str) -> bool:
    """True if yesterday's streak was not maintained — today's tasks become urgent."""
    yesterday_iso = (date.today() - timedelta(days=1)).isoformat()
    log = db.query(StreakLog).filter(StreakLog.date == yesterday_iso).first()
    if log is None:
        return False
    return not bool(log.streak_maintained)


# @tag REMINDER HOME_DASHBOARD
def _stale_lesson(db: Session) -> AcademySession | None:
    """
    Return any in-progress AcademySession whose last activity was 2+ days ago.
    Used to warn that a session is approaching the auto-reset boundary.
    """
    cutoff = (date.today() - timedelta(days=2)).isoformat()
    try:
        return (
            db.query(AcademySession)
              .filter(AcademySession.is_completed == False)  # noqa: E712
              .filter(AcademySession.is_reset == False)      # noqa: E712
              .filter(AcademySession.started_date <= cutoff)
              .order_by(AcademySession.started_date.asc())
              .first()
        )
    except Exception:
        return None


# @tag REMINDER HOME_DASHBOARD
def _pending_day_off(db: Session) -> DayOffRequest | None:
    """Return the most recent pending Day Off request, if any."""
    try:
        return (
            db.query(DayOffRequest)
              .filter(DayOffRequest.status == "pending")
              .order_by(DayOffRequest.created_at.desc())
              .first()
        )
    except Exception:
        return None


# @tag REMINDER HOME_DASHBOARD
def _recent_lesson_reset(db: Session) -> GrowthEvent | None:
    """Return the most recent lesson_reset event from the last 24h."""
    cutoff = (datetime.now() - timedelta(days=1)).isoformat(timespec="seconds")
    try:
        return (
            db.query(GrowthEvent)
              .filter(GrowthEvent.event_type == "lesson_reset")
              .filter(GrowthEvent.created_at >= cutoff)
              .order_by(GrowthEvent.created_at.desc())
              .first()
        )
    except Exception:
        return None


# @tag REMINDER HOME_DASHBOARD
@router.get("/today")
def today_reminders(db: Session = Depends(get_db)) -> List[dict]:
    """
    Return today's reminder banners for the home dashboard.

    Each banner: {"key": str, "severity": "info"|"warning"|"danger", "message": str}
    Severity controls banner color in the frontend.
    """
    banners: List[dict] = []
    today_iso = date.today().isoformat()

    # 1. Review due — the most common nudge
    due = _review_due_count(db, today_iso)
    if due > 0:
        banners.append({
            "key": "review_due",
            "severity": "info",
            "message": f"⏰ {due} word{'s' if due != 1 else ''} ready for review today!",
        })

    # 2. Streak at risk — yesterday wasn't maintained
    if _streak_at_risk(db, today_iso):
        banners.append({
            "key": "streak_at_risk",
            "severity": "warning",
            "message": "🔥 Your streak is at risk — finish today's tasks to keep it alive!",
        })

    # 3. Stale academy lesson — auto-reset coming
    stale = _stale_lesson(db)
    if stale is not None:
        banners.append({
            "key": "stale_lesson",
            "severity": "warning",
            "message": f"📕 Lesson '{stale.lesson}' has been idle for 2+ days. Continue today or it'll reset!",
        })

    # 4. Lesson reset notification (last 24h)
    reset = _recent_lesson_reset(db)
    if reset is not None:
        banners.append({
            "key": "lesson_reset",
            "severity": "danger",
            "message": f"🔄 {reset.title or 'A lesson was reset'}. Time to start fresh!",
        })

    # 5. Pending day-off request awaiting parent decision
    pending = _pending_day_off(db)
    if pending is not None:
        banners.append({
            "key": "day_off_pending",
            "severity": "info",
            "message": f"🏖️ Day off request for {pending.request_date} is pending parent approval.",
        })

    return banners
