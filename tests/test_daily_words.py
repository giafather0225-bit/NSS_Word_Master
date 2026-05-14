"""Tests for routers/daily_words.py — Daily Words 7-day cycle API.

daily_words.py is DUX-protected (CLAUDE.md rule 14) — these tests are
additive only, no router changes.
"""
from datetime import date, timedelta

import pytest

from backend.models import XPLog, DailyWordsProgress, WordReview
from backend.models.gamification import StreakLog


@pytest.fixture(autouse=True)
def _clean_tables(db_session):
    def _wipe():
        for model in (XPLog, DailyWordsProgress, WordReview, StreakLog):
            db_session.query(model).delete()
        db_session.commit()
    _wipe()
    yield
    _wipe()


def _seed_progress(db, cycle_day=1, grade="grade_3"):
    """Seed a progress row whose cycle_start places today at `cycle_day`."""
    start = (date.today() - timedelta(days=cycle_day - 1)).isoformat()
    p = DailyWordsProgress(
        grade=grade, cycle_start=start, word_index=0,
        test_words_json="[]", daily_learned=0, last_study_date=None,
    )
    db.add(p)
    db.commit()
    return p


# ── GET /status ───────────────────────────────────────────────

def test_status_creates_progress(client, db_session):
    r = client.get("/api/daily-words/status")
    assert r.status_code == 200
    body = r.json()
    assert body["cycle_day"] == 1
    assert body["day_label"] == "Placement Test"
    assert db_session.query(DailyWordsProgress).count() == 1


# ── GET /today ────────────────────────────────────────────────

def test_today_day1_placement(client):
    body = client.get("/api/daily-words/today").json()
    assert body["cycle_day"] == 1
    assert "words" in body
    assert body["daily_target"] == 10


# ── POST /day1-result ─────────────────────────────────────────

def test_day1_result_records_failures(client):
    r = client.post("/api/daily-words/day1-result",
                    json={"failed_words": ["alpha", "beta"]})
    assert r.status_code == 200
    assert r.json() == {"ok": True, "failed_count": 2}


# ── POST /complete ────────────────────────────────────────────

def test_complete_awards_xp(client):
    r = client.post("/api/daily-words/complete", json={"learned_count": 10})
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["xp_awarded"] == 10  # daily_words_complete (XP_RULES_DEFAULT)


# ── GET /weekly-test ──────────────────────────────────────────

def test_weekly_test_rejected_when_not_day7(client):
    r = client.get("/api/daily-words/weekly-test")
    assert r.status_code == 400


def test_weekly_test_available_on_day7(client, db_session):
    _seed_progress(db_session, cycle_day=7)
    r = client.get("/api/daily-words/weekly-test")
    assert r.status_code == 200
    assert r.json()["cycle_day"] == 7


# ── POST /weekly-test/result ──────────────────────────────────

def test_weekly_test_result_pass_awards_xp(client, db_session):
    _seed_progress(db_session, cycle_day=7)
    r = client.post("/api/daily-words/weekly-test/result",
                    json={"correct_count": 10, "total_count": 10})
    assert r.status_code == 200
    body = r.json()
    assert body["passed"] is True
    assert body["xp_awarded"] == 10  # weekly_test_pass


def test_weekly_test_result_fail_no_xp(client, db_session):
    _seed_progress(db_session, cycle_day=7)
    body = client.post("/api/daily-words/weekly-test/result",
                       json={"correct_count": 4, "total_count": 10}).json()
    assert body["passed"] is False
    assert body["xp_awarded"] == 0
