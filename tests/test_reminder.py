"""Tests for backend/routers/reminder.py — home dashboard reminder banners.

Covers GET /api/reminders/today: empty-DB shape, banner derivation from
seeded StreakLog / DayOffRequest rows, and the documented banner schema
(key / severity / message).
"""

from datetime import date, timedelta

import pytest


@pytest.fixture(autouse=True)
def _clean_reminder_tables(db_session):
    """Wipe reminder-source tables before/after each test (StaticPool persistence)."""
    from backend.models import (StreakLog, WordReview, AcademySession,
                                GrowthEvent, DayOffRequest)
    models = (StreakLog, WordReview, AcademySession, GrowthEvent, DayOffRequest)
    for m in models:
        db_session.query(m).delete()
    db_session.commit()
    yield
    for m in models:
        db_session.query(m).delete()
    db_session.commit()


# ── GET /api/reminders/today ──────────────────────────────────────────

def test_empty_db_returns_list(client):
    """No seeded data → endpoint returns a (possibly empty) list, not a 500."""
    resp = client.get("/api/reminders/today")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_banner_schema(client, db_session):
    """Every returned banner carries key / severity / message."""
    # Seed a pending day-off → guarantees at least one banner
    from datetime import datetime, timezone
    from backend.models import DayOffRequest
    db_session.add(DayOffRequest(
        request_date="2026-12-01", reason="trip", status="pending",
        created_at=datetime.now(timezone.utc).isoformat(),
    ))
    db_session.commit()

    banners = client.get("/api/reminders/today").json()
    assert len(banners) >= 1
    for b in banners:
        assert "key" in b
        assert "message" in b
        assert b["severity"] in ("info", "warning", "danger")


def test_pending_day_off_banner(client, db_session):
    """A pending day-off request surfaces the day_off_pending banner."""
    from datetime import datetime, timezone
    from backend.models import DayOffRequest
    db_session.add(DayOffRequest(
        request_date="2026-12-25", reason="holiday", status="pending",
        created_at=datetime.now(timezone.utc).isoformat(),
    ))
    db_session.commit()

    banners = client.get("/api/reminders/today").json()
    keys = {b["key"] for b in banners}
    assert "day_off_pending" in keys


def test_approved_day_off_no_banner(client, db_session):
    """An approved (non-pending) day-off does NOT produce a pending banner."""
    from datetime import datetime, timezone
    from backend.models import DayOffRequest
    db_session.add(DayOffRequest(
        request_date="2026-12-25", reason="holiday", status="approved",
        created_at=datetime.now(timezone.utc).isoformat(),
    ))
    db_session.commit()

    banners = client.get("/api/reminders/today").json()
    keys = {b["key"] for b in banners}
    assert "day_off_pending" not in keys


def test_streak_at_risk_banner(client, db_session):
    """Yesterday's StreakLog with streak_maintained=False → streak_at_risk banner."""
    from backend.models import StreakLog
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    db_session.add(StreakLog(date=yesterday, streak_maintained=False))
    db_session.commit()

    banners = client.get("/api/reminders/today").json()
    keys = {b["key"] for b in banners}
    assert "streak_at_risk" in keys
    risk = next(b for b in banners if b["key"] == "streak_at_risk")
    assert risk["severity"] == "warning"


def test_maintained_streak_no_risk_banner(client, db_session):
    """Yesterday maintained → no streak_at_risk banner."""
    from backend.models import StreakLog
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    db_session.add(StreakLog(date=yesterday, streak_maintained=True))
    db_session.commit()

    banners = client.get("/api/reminders/today").json()
    keys = {b["key"] for b in banners}
    assert "streak_at_risk" not in keys
