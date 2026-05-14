"""Tests for backend/routers/goals.py — weekly learning goals.

Covers the read endpoint (goals + live progress) and the PIN-gated
update endpoint (key validation, target range, 404, happy path).

The parent PIN guard falls back to DEFAULT_PIN "0000" when no `pin`
row exists in AppConfig — tests send that in the X-Parent-Pin header.
"""

from datetime import datetime

import pytest

_PIN_HEADER = {"X-Parent-Pin": "0000"}


@pytest.fixture(autouse=True)
def _clean_goals_tables(db_session):
    """Wipe goal-related tables before/after each test.

    The in-memory SQLite shares one connection (StaticPool) so endpoint
    db.commit() calls persist across the session — without this, seeded
    WeeklyGoal rows collide on the UNIQUE(key) constraint and stray XPLog
    rows pollute the live-progress computation.
    """
    from backend.models import XPLog, WordAttempt, LearningLog
    from backend.models.goals import WeeklyGoal
    for model in (WeeklyGoal, XPLog, WordAttempt, LearningLog):
        db_session.query(model).delete()
    db_session.commit()
    yield
    for model in (WeeklyGoal, XPLog, WordAttempt, LearningLog):
        db_session.query(model).delete()
    db_session.commit()


def _seed_goal(db, key, label, target=100, is_active=1):
    from backend.models.goals import WeeklyGoal
    g = WeeklyGoal(key=key, label=label, target=target, is_active=is_active,
                   updated_at=datetime.now().isoformat())
    db.add(g)
    db.commit()
    return g


# ── GET /api/goals/weekly ─────────────────────────────────────────────

def test_weekly_goals_empty(client):
    """No seeded goals → empty list with valid envelope."""
    resp = client.get("/api/goals/weekly")
    assert resp.status_code == 200
    body = resp.json()
    for key in ("week_start", "goals", "total_active", "total_achieved"):
        assert key in body
    assert body["goals"] == []
    assert body["total_active"] == 0


def test_weekly_goals_with_seed(client, db_session):
    """Seeded goals appear with computed pct + achieved flags."""
    _seed_goal(db_session, "words_correct", "Words Correct", target=50)
    _seed_goal(db_session, "xp_earned", "XP Earned", target=200)
    resp = client.get("/api/goals/weekly")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["goals"]) == 2
    keys = {g["key"] for g in body["goals"]}
    assert keys == {"words_correct", "xp_earned"}
    for g in body["goals"]:
        # No activity seeded → current 0, pct 0, not achieved
        assert g["current"] == 0
        assert g["pct"] == 0
        assert g["achieved"] is False
        assert g["is_active"] is True
    assert body["total_active"] == 2
    assert body["total_achieved"] == 0


def test_weekly_goals_progress_reflects_xp(client, db_session):
    """Seeded XPLog rows this week count toward the xp_earned goal."""
    from datetime import date
    from backend.models import XPLog
    _seed_goal(db_session, "xp_earned", "XP Earned", target=10)
    today = date.today().isoformat()
    db_session.add(XPLog(action="stage_complete", xp_amount=15,
                         detail="", earned_date=today,
                         created_at=datetime.now().isoformat()))
    db_session.commit()

    resp = client.get("/api/goals/weekly")
    goal = next(g for g in resp.json()["goals"] if g["key"] == "xp_earned")
    assert goal["current"] >= 15
    assert goal["achieved"] is True   # 15 >= target 10


# ── PUT /api/goals/weekly/{key} — auth + validation ───────────────────

def test_update_goal_no_pin_403(client, db_session):
    _seed_goal(db_session, "xp_earned", "XP Earned")
    resp = client.put("/api/goals/weekly/xp_earned", json={"target": 300})
    assert resp.status_code == 403


def test_update_goal_unknown_key_400(client):
    resp = client.put("/api/goals/weekly/bogus_key",
                      json={"target": 100}, headers=_PIN_HEADER)
    assert resp.status_code == 400


def test_update_goal_target_out_of_range_400(client):
    resp = client.put("/api/goals/weekly/xp_earned",
                      json={"target": 99999}, headers=_PIN_HEADER)
    assert resp.status_code == 400


def test_update_goal_negative_target_400(client):
    resp = client.put("/api/goals/weekly/xp_earned",
                      json={"target": -5}, headers=_PIN_HEADER)
    assert resp.status_code == 400


def test_update_goal_not_found_404(client):
    """Valid key + PIN but no WeeklyGoal row → 404."""
    resp = client.put("/api/goals/weekly/streak_days",
                      json={"target": 7}, headers=_PIN_HEADER)
    assert resp.status_code == 404


# ── PUT /api/goals/weekly/{key} — happy path ──────────────────────────

def test_update_goal_success(client, db_session):
    _seed_goal(db_session, "study_minutes", "Study Minutes", target=60)
    resp = client.put("/api/goals/weekly/study_minutes",
                      json={"target": 90, "is_active": False},
                      headers=_PIN_HEADER)
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert body["target"] == 90
    assert body["is_active"] is False

    # Change is persisted — visible via GET
    listing = client.get("/api/goals/weekly")
    goal = next(g for g in listing.json()["goals"] if g["key"] == "study_minutes")
    assert goal["target"] == 90
    assert goal["is_active"] is False
