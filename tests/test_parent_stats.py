"""Tests for backend/routers/parent_stats.py — parent dashboard read-only stats.

Covers overview / summary / activity / stage-stats / word-stats. All are
read-only aggregate endpoints — tests verify the documented shape on an
empty DB and that seeded XPLog / LearningLog / WordAttempt rows are
reflected in the aggregates.
"""

from datetime import date, datetime, timedelta

import pytest


@pytest.fixture(autouse=True)
def _clean_stats_tables(db_session):
    """Wipe stats-source tables before/after each test (StaticPool persistence)."""
    from backend.models import LearningLog, WordAttempt, XPLog, Progress
    models = (LearningLog, WordAttempt, XPLog, Progress)
    for m in models:
        db_session.query(m).delete()
    db_session.commit()
    yield
    for m in models:
        db_session.query(m).delete()
    db_session.commit()


def _seed_xplog(db, action="stage_complete", amount=5, earned_date=None):
    from backend.models import XPLog
    db.add(XPLog(action=action, xp_amount=amount, detail="",
                 earned_date=earned_date or date.today().isoformat(),
                 created_at=datetime.now().isoformat()))
    db.commit()


# ── GET /api/parent/overview ──────────────────────────────────────────

def test_overview_empty_shape(client):
    resp = client.get("/api/parent/overview")
    assert resp.status_code == 200
    body = resp.json()
    for key in ("total_xp", "today_xp", "today_by_subject", "streak",
                "words_known", "recent_logs"):
        assert key in body
    assert body["total_xp"] == 0
    for subj in ("english", "math", "diary"):
        assert subj in body["today_by_subject"]
        assert body["today_by_subject"][subj] == {"xp": 0, "count": 0}
    assert body["recent_logs"] == []


def test_overview_today_by_subject_buckets_xp(client, db_session):
    """A math_lesson_complete XPLog today lands in the math bucket."""
    _seed_xplog(db_session, action="math_lesson_complete", amount=15)
    _seed_xplog(db_session, action="stage_complete", amount=5)
    body = client.get("/api/parent/overview").json()
    assert body["today_by_subject"]["math"]["xp"] == 15
    assert body["today_by_subject"]["math"]["count"] == 1
    assert body["today_by_subject"]["english"]["xp"] == 5


# ── GET /api/parent/summary ───────────────────────────────────────────

def test_summary_empty_shape(client):
    resp = client.get("/api/parent/summary")
    assert resp.status_code == 200
    body = resp.json()
    for key in ("total_words_learned", "total_xp", "current_level",
                "current_streak", "longest_streak", "total_study_sessions",
                "total_study_minutes", "lessons_completed", "tests_passed",
                "average_test_score", "words_known"):
        assert key in body
    assert body["total_xp"] == 0
    assert body["current_level"] == 1


def test_summary_counts_tests_passed(client, db_session):
    _seed_xplog(db_session, action="final_test_pass", amount=20)
    body = client.get("/api/parent/summary").json()
    assert body["tests_passed"] >= 1
    assert body["total_xp"] >= 20


# ── GET /api/parent/activity ──────────────────────────────────────────

def test_activity_default_7_days(client):
    resp = client.get("/api/parent/activity")
    assert resp.status_code == 200
    body = resp.json()
    assert "daily" in body
    assert len(body["daily"]) == 7
    for day in body["daily"]:
        for key in ("date", "words", "xp", "minutes", "sessions"):
            assert key in day


def test_activity_days_param(client):
    body = client.get("/api/parent/activity?days=14").json()
    assert len(body["daily"]) == 14


def test_activity_days_out_of_range_422(client):
    assert client.get("/api/parent/activity?days=0").status_code == 422
    assert client.get("/api/parent/activity?days=999").status_code == 422


def test_activity_reflects_xp(client, db_session):
    """XP earned today shows up on today's activity row."""
    _seed_xplog(db_session, amount=30)
    body = client.get("/api/parent/activity?days=1").json()
    assert body["daily"][0]["xp"] >= 30


# ── GET /api/parent/stage-stats ───────────────────────────────────────

def test_stage_stats_empty(client):
    resp = client.get("/api/parent/stage-stats")
    assert resp.status_code == 200
    assert resp.json() == {"stages": {}}


def test_stage_stats_reflects_learning_log(client, db_session):
    """A LearningLog row produces a per-stage entry."""
    from backend.models import LearningLog
    db_session.add(LearningLog(
        subject="English", textbook="Voca_8000", lesson="Lesson_01",
        stage="A", correct_count=8, word_count=10, duration_sec=120,
        completed_at=datetime.now().isoformat(),
    ))
    db_session.commit()
    body = client.get("/api/parent/stage-stats").json()
    # Stage "A" maps to label "word_match"
    assert "word_match" in body["stages"]
    assert body["stages"]["word_match"]["completions"] == 1


# ── GET /api/parent/word-stats ────────────────────────────────────────

def test_word_stats_empty(client):
    resp = client.get("/api/parent/word-stats")
    assert resp.status_code == 200
    # Returns a dict payload — just verify it doesn't 500 on empty DB
    assert isinstance(resp.json(), dict)
