"""Tests for backend/routers/xp.py — XP summary, award, streak, tasks.

Covers the read endpoints (summary / streak status / weekly chart /
today's tasks) and the POST /api/xp/award flow including unknown-action
rejection and the atomic XP-log + streak commit path.
"""

from datetime import date, datetime, timedelta

import pytest


@pytest.fixture(autouse=True)
def _clean_xp_tables(db_session):
    """Wipe XP/streak/task tables before/after each test.

    The in-memory SQLite shares one connection (StaticPool) so endpoint
    db.commit() calls persist across the session — without this, XPLog
    rows leak into today_xp/dedup checks and StreakLog rows make
    streak-status assertions flaky.
    """
    from backend.models import (XPLog, StreakLog, TaskSetting, WordReview,
                                DiaryEntry, DailyWordsProgress)
    models = (XPLog, StreakLog, TaskSetting, WordReview, DiaryEntry,
              DailyWordsProgress)
    for model in models:
        db_session.query(model).delete()
    db_session.commit()
    yield
    for model in models:
        db_session.query(model).delete()
    db_session.commit()


def _seed_xplog(db, action="stage_complete", amount=5, earned_date=None):
    from backend.models import XPLog
    if earned_date is None:
        earned_date = date.today().isoformat()
    db.add(XPLog(action=action, xp_amount=amount, detail="",
                 earned_date=earned_date,
                 created_at=datetime.now().isoformat()))
    db.commit()


# ── GET /api/xp/summary ───────────────────────────────────────────────

def test_xp_summary_empty(client):
    resp = client.get("/api/xp/summary")
    assert resp.status_code == 200
    body = resp.json()
    for key in ("total_xp", "today_xp", "level", "streak_days",
                "streak_best", "words_known"):
        assert key in body
    assert body["total_xp"] == 0
    assert body["level"] == 1   # total // 100 + 1


def test_xp_summary_reflects_seeded_xp(client, db_session):
    _seed_xplog(db_session, action="stage_complete", amount=120)
    resp = client.get("/api/xp/summary")
    body = resp.json()
    assert body["total_xp"] >= 120
    assert body["today_xp"] >= 120
    assert body["level"] >= 2   # 120 // 100 + 1 = 2


def test_xp_summary_old_xp_not_in_today(client, db_session):
    """XP earned on a past date counts toward total but not today_xp."""
    old_date = (date.today() - timedelta(days=30)).isoformat()
    _seed_xplog(db_session, action="stage_complete", amount=50, earned_date=old_date)
    resp = client.get("/api/xp/summary")
    body = resp.json()
    assert body["total_xp"] >= 50
    assert body["today_xp"] == 0


# ── POST /api/xp/award ────────────────────────────────────────────────

def test_award_unknown_action_400(client):
    resp = client.post("/api/xp/award", json={"action": "not_a_real_action"})
    assert resp.status_code == 400


def test_award_valid_action(client):
    resp = client.post("/api/xp/award",
                       json={"action": "stage_complete", "detail": "lesson1"})
    assert resp.status_code == 200
    body = resp.json()
    for key in ("xp_awarded", "bonus_xp", "total_xp", "level", "streak_days"):
        assert key in body
    assert body["xp_awarded"] > 0


def test_award_dedup_same_day(client):
    """stage_complete is once-per-day — second award returns 0."""
    first = client.post("/api/xp/award", json={"action": "stage_complete"})
    second = client.post("/api/xp/award", json={"action": "stage_complete"})
    assert first.json()["xp_awarded"] > 0
    assert second.json()["xp_awarded"] == 0


def test_award_review_complete_marks_streak(client):
    """review_complete action triggers the streak side-effect without error."""
    resp = client.post("/api/xp/award", json={"action": "review_complete"})
    assert resp.status_code == 200
    # After awarding, streak status should show review done
    status = client.get("/api/streak/status").json()
    assert status["today_review_done"] is True


# ── GET /api/streak/status ────────────────────────────────────────────

def test_streak_status_empty(client):
    resp = client.get("/api/streak/status")
    assert resp.status_code == 200
    body = resp.json()
    for key in ("streak_days", "today_review_done",
                "today_daily_words_done", "today_streak_maintained"):
        assert key in body
    assert body["streak_days"] == 0
    assert body["today_review_done"] is False


# ── GET /api/xp/weekly ────────────────────────────────────────────────

def test_xp_weekly_returns_seven_days(client):
    resp = client.get("/api/xp/weekly")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    assert len(body) == 7
    for day in body:
        for key in ("date", "label", "value", "maintained"):
            assert key in day


# ── GET /api/tasks/today ──────────────────────────────────────────────

def test_tasks_today_returns_list(client):
    resp = client.get("/api/tasks/today")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)


def test_tasks_today_with_active_task_settings(client, db_session):
    """Active TaskSetting rows surface as tasks in the today list."""
    from backend.models import TaskSetting
    db_session.add(TaskSetting(task_key="review", is_active=True))
    db_session.commit()
    resp = client.get("/api/tasks/today")
    assert resp.status_code == 200
    keys = {t.get("key") for t in resp.json()}
    assert "review" in keys
