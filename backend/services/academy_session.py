"""
services/academy_session.py — AcademySession lifecycle + 2-day gap auto-reset
Section: English / Academy
Dependencies: models.py (AcademySession, GrowthEvent)
"""

from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

try:
    from ..models import AcademySession, GrowthEvent
except ImportError:
    from models import AcademySession, GrowthEvent  # type: ignore


MAX_IDLE_DAYS = 2  # day 3 since last activity → reset


# @tag ACADEMY SYSTEM
def upsert_session(
    db: Session, subject: str, textbook: str, lesson: str
) -> AcademySession:
    """Create or re-open an AcademySession for the (subject, textbook, lesson) tuple.

    If an in-progress row exists, refresh last_active_date. If a row was previously
    reset (is_reset=True), re-open it as a fresh session. Completed rows are left
    alone and a new row is created.
    """
    today = date.today().isoformat()
    sess = (
        db.query(AcademySession)
        .filter(
            AcademySession.subject == subject,
            AcademySession.textbook == textbook,
            AcademySession.lesson == lesson,
            AcademySession.is_completed == False,  # noqa: E712
        )
        .order_by(AcademySession.id.desc())
        .first()
    )
    if sess is not None:
        if sess.is_reset:
            sess.is_reset = False
            sess.started_date = today
            sess.current_stage = "PREVIEW"
        sess.last_active_date = today
        db.commit()
        return sess

    sess = AcademySession(
        subject=subject,
        textbook=textbook,
        lesson=lesson,
        started_date=today,
        last_active_date=today,
        current_stage="PREVIEW",
        is_completed=False,
        is_reset=False,
    )
    db.add(sess)
    db.commit()
    db.refresh(sess)
    return sess


# @tag ACADEMY SYSTEM
def touch_session(
    db: Session,
    textbook: str,
    lesson: str,
    stage: Optional[str] = None,
    subject: str = "English",
) -> None:
    """Record activity for a session: refresh last_active_date and optionally advance stage.

    Safe no-op if no matching in-progress session exists (caller may not have
    started one — this shouldn't happen for Academy stages, but we fail soft).
    """
    today = date.today().isoformat()
    sess = (
        db.query(AcademySession)
        .filter(
            AcademySession.subject == subject,
            AcademySession.textbook == textbook,
            AcademySession.lesson == lesson,
            AcademySession.is_completed == False,  # noqa: E712
        )
        .order_by(AcademySession.id.desc())
        .first()
    )
    if sess is None:
        sess = AcademySession(
            subject=subject, textbook=textbook, lesson=lesson,
            started_date=today, last_active_date=today,
            current_stage=stage or "PREVIEW",
        )
        db.add(sess)
        db.commit()
        return

    sess.last_active_date = today
    if sess.is_reset:
        sess.is_reset = False
        sess.started_date = today
    if stage:
        sess.current_stage = stage
    db.commit()


# @tag ACADEMY SYSTEM
def enforce_session_gap(db: Session) -> int:
    """Reset any in-progress session idle for more than MAX_IDLE_DAYS days.

    For each reset: mark is_reset=True and record a GrowthEvent('lesson_reset').
    Returns the number of sessions reset.
    """
    cutoff = (date.today() - timedelta(days=MAX_IDLE_DAYS)).isoformat()
    now_iso = datetime.now().isoformat(timespec="seconds")
    today_iso = date.today().isoformat()

    stale = (
        db.query(AcademySession)
        .filter(AcademySession.is_completed == False)  # noqa: E712
        .filter(AcademySession.is_reset == False)      # noqa: E712
        .filter(AcademySession.last_active_date != None)  # noqa: E711
        .filter(AcademySession.last_active_date < cutoff)
        .all()
    )
    if not stale:
        return 0

    for s in stale:
        s.is_reset = True
        db.add(GrowthEvent(
            event_type="lesson_reset",
            title=f"Lesson '{s.lesson}' was reset",
            detail=f"{s.textbook}/{s.lesson} idle since {s.last_active_date}",
            event_date=today_iso,
            created_at=now_iso,
        ))
    db.commit()
    return len(stale)
