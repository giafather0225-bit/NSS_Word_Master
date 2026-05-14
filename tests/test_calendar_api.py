"""Tests for backend/routers/calendar_api.py — monthly calendar markers.

Covers the single endpoint GET /api/calendar/{year}/{month}: month/year
range validation, the per-day object shape, day count correctness, and
marker derivation from seeded DiaryEntry / DayOffRequest / StreakLog rows.
"""

import pytest


@pytest.fixture(autouse=True)
def _clean_calendar_tables(db_session):
    """Wipe calendar-source tables before/after each test (StaticPool persistence)."""
    from backend.models import DiaryEntry, StreakLog, DayOffRequest, TaskSetting, XPLog
    models = (DiaryEntry, StreakLog, DayOffRequest, TaskSetting, XPLog)
    for m in models:
        db_session.query(m).delete()
    db_session.commit()
    yield
    for m in models:
        db_session.query(m).delete()
    db_session.commit()


# ── Validation ────────────────────────────────────────────────────────

def test_month_out_of_range_400(client):
    assert client.get("/api/calendar/2026/0").status_code == 400
    assert client.get("/api/calendar/2026/13").status_code == 400


def test_year_out_of_range_400(client):
    assert client.get("/api/calendar/1999/6").status_code == 400
    assert client.get("/api/calendar/2200/6").status_code == 400


# ── Shape + day count ─────────────────────────────────────────────────

def test_returns_correct_day_count(client):
    """February 2026 has 28 days; July has 31."""
    feb = client.get("/api/calendar/2026/2")
    assert feb.status_code == 200
    assert len(feb.json()) == 28

    jul = client.get("/api/calendar/2026/7")
    assert len(jul.json()) == 31


def test_day_object_shape(client):
    body = client.get("/api/calendar/2026/6").json()
    assert len(body) == 30
    for day in body:
        for key in ("date", "streak", "journal", "day_off", "all_done", "marker"):
            assert key in day
    # First day's date string is well-formed
    assert body[0]["date"] == "2026-06-01"


def test_empty_month_all_blank_markers(client):
    """No seeded data → every day has blank journal/streak/day_off flags."""
    body = client.get("/api/calendar/2026/6").json()
    for day in body:
        assert day["journal"] is False
        assert day["day_off"] is False
        assert day["streak"] is False
        assert day["all_done"] is False


# ── Marker derivation ─────────────────────────────────────────────────

def test_journal_marker(client, db_session):
    """A DiaryEntry on a date flips that day's journal flag + 📝 marker."""
    from datetime import datetime, timezone
    from backend.models import DiaryEntry
    db_session.add(DiaryEntry(
        entry_date="2026-06-10", content="dear diary",
        created_at=datetime.now(timezone.utc).isoformat(),
    ))
    db_session.commit()

    body = client.get("/api/calendar/2026/6").json()
    day10 = next(d for d in body if d["date"] == "2026-06-10")
    assert day10["journal"] is True
    assert day10["marker"] == "📝"


def test_day_off_marker_takes_priority(client, db_session):
    """An approved DayOffRequest yields the 🏖️ marker (highest priority)."""
    from datetime import datetime, timezone
    from backend.models import DayOffRequest
    db_session.add(DayOffRequest(
        request_date="2026-06-20", reason="vacation", status="approved",
        created_at=datetime.now(timezone.utc).isoformat(),
    ))
    db_session.commit()

    body = client.get("/api/calendar/2026/6").json()
    day20 = next(d for d in body if d["date"] == "2026-06-20")
    assert day20["day_off"] is True
    assert day20["marker"] == "🏖️"


def test_pending_day_off_not_marked(client, db_session):
    """A pending (not approved) day-off request does NOT set the day_off flag."""
    from datetime import datetime, timezone
    from backend.models import DayOffRequest
    db_session.add(DayOffRequest(
        request_date="2026-06-25", reason="maybe", status="pending",
        created_at=datetime.now(timezone.utc).isoformat(),
    ))
    db_session.commit()

    body = client.get("/api/calendar/2026/6").json()
    day25 = next(d for d in body if d["date"] == "2026-06-25")
    assert day25["day_off"] is False
