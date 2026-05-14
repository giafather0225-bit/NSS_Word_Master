"""Tests for backend/routers/parent_streak.py — parent dashboard streak.

Covers the read-only streak payload and the two PIN-gated mutations
(streak-rule update with validation, streak-recalc with day-range
validation). PIN falls back to DEFAULT_PIN "0000" on the test host.
"""

from datetime import date, timedelta

import pytest

_PIN_HEADER = {"X-Parent-Pin": "0000"}


@pytest.fixture(autouse=True)
def _clean_streak_tables(db_session):
    """Wipe streak-source tables before/after each test (StaticPool persistence)."""
    from backend.models import StreakLog, DayOffRequest, AppConfig
    def _wipe():
        for m in (StreakLog, DayOffRequest):
            db_session.query(m).delete()
        db_session.query(AppConfig).filter(
            AppConfig.key.in_(("streak_subjects", "streak_mode", "pin"))
        ).delete(synchronize_session=False)
        db_session.commit()
    _wipe()
    yield
    _wipe()


# ── GET /api/parent/streak ────────────────────────────────────────────

def test_streak_empty_shape(client):
    resp = client.get("/api/parent/streak")
    assert resp.status_code == 200
    body = resp.json()
    for key in ("current", "longest", "rule", "last_30d",
                "freeze_this_month", "milestones"):
        assert key in body
    assert body["current"] == 0
    assert body["longest"] == 0
    assert len(body["last_30d"]) == 30
    assert "subjects" in body["rule"] and "mode" in body["rule"]


def test_streak_longest_from_logs(client, db_session):
    """A 3-day maintained run shows longest=3."""
    from backend.models import StreakLog
    today = date.today()
    for i in range(3):
        d = (today - timedelta(days=i)).isoformat()
        db_session.add(StreakLog(date=d, streak_maintained=True))
    db_session.commit()
    body = client.get("/api/parent/streak").json()
    assert body["longest"] >= 3


def test_streak_last_30d_marks_day_off(client, db_session):
    """An approved day-off in the window flips that day's day_off flag."""
    from datetime import datetime, timezone
    from backend.models import DayOffRequest
    target = (date.today() - timedelta(days=3)).isoformat()
    db_session.add(DayOffRequest(
        request_date=target, reason="trip", status="approved",
        created_at=datetime.now(timezone.utc).isoformat(),
    ))
    db_session.commit()
    body = client.get("/api/parent/streak").json()
    day = next(d for d in body["last_30d"] if d["date"] == target)
    assert day["day_off"] is True


# ── POST /api/parent/streak-rule ──────────────────────────────────────

def test_streak_rule_no_pin_403(client):
    resp = client.post("/api/parent/streak-rule",
                       json={"subjects": ["english"], "mode": "all"})
    assert resp.status_code == 403


def test_streak_rule_empty_subjects_400(client):
    resp = client.post("/api/parent/streak-rule",
                       json={"subjects": ["bogus"], "mode": "all"},
                       headers=_PIN_HEADER)
    assert resp.status_code == 400


def test_streak_rule_bad_mode_400(client):
    resp = client.post("/api/parent/streak-rule",
                       json={"subjects": ["english"], "mode": "sometimes"},
                       headers=_PIN_HEADER)
    assert resp.status_code == 400


def test_streak_rule_success(client):
    resp = client.post("/api/parent/streak-rule",
                       json={"subjects": ["english", "math"], "mode": "any"},
                       headers=_PIN_HEADER)
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert body["subjects"] == ["english", "math"]
    assert body["mode"] == "any"
    # Reflected in the GET payload
    rule = client.get("/api/parent/streak").json()["rule"]
    assert rule["mode"] == "any"


# ── POST /api/parent/streak-recalc ────────────────────────────────────

def test_streak_recalc_no_pin_403(client):
    resp = client.post("/api/parent/streak-recalc")
    assert resp.status_code == 403


def test_streak_recalc_days_out_of_range_422(client):
    """days query param is ge=1, le=90."""
    assert client.post("/api/parent/streak-recalc?days=0",
                       headers=_PIN_HEADER).status_code == 422
    assert client.post("/api/parent/streak-recalc?days=999",
                       headers=_PIN_HEADER).status_code == 422


def test_streak_recalc_success(client):
    resp = client.post("/api/parent/streak-recalc?days=7", headers=_PIN_HEADER)
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert "re_evaluated" in body
