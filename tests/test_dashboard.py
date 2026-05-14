"""Tests for backend/routers/dashboard.py — parent dashboard aggregates.

Covers the three read-only aggregate endpoints: stats, per-textbook
detail, and the analytics bundle. All endpoints must return a valid
shape on an empty DB and reflect seeded StudyItem / Progress rows.
"""

from datetime import datetime, timezone

import pytest


@pytest.fixture(autouse=True)
def _clean_dashboard_tables(db_session):
    """Wipe dashboard-source tables before/after each test.

    The StaticPool in-memory DB persists committed rows across the
    session — without this, seeded StudyItem/Progress rows leak between
    tests and break the count assertions.
    """
    from backend.models import StudyItem, Progress
    for model in (StudyItem, Progress):
        db_session.query(model).delete()
    db_session.commit()
    yield
    for model in (StudyItem, Progress):
        db_session.query(model).delete()
    db_session.commit()


def _seed_study_items(db, textbook="Voca_8000", lesson="Lesson_01", n=3):
    from backend.models import StudyItem
    db.add_all([
        StudyItem(subject="English", textbook=textbook, lesson=lesson,
                  source_type="manual", question=f"def {i}", answer=f"word{i}")
        for i in range(n)
    ])
    db.commit()


# ── GET /api/dashboard/stats ──────────────────────────────────────────

def test_stats_empty(client):
    resp = client.get("/api/dashboard/stats")
    assert resp.status_code == 200
    body = resp.json()
    for key in ("total_words", "textbook_count", "lesson_count",
                "best_streak", "textbooks"):
        assert key in body
    assert isinstance(body["textbooks"], list)


def test_stats_reflects_seeded_items(client, db_session):
    _seed_study_items(db_session, textbook="Voca_8000", lesson="Lesson_01", n=5)
    resp = client.get("/api/dashboard/stats")
    body = resp.json()
    assert body["total_words"] >= 5
    tb_names = {t["name"] for t in body["textbooks"]}
    assert "Voca_8000" in tb_names


def test_stats_best_streak_from_progress(client, db_session):
    from backend.models import Progress
    db_session.add(Progress(
        subject="English", textbook="Voca_8000", lesson="Lesson_01",
        current_index=0, best_streak=12,
    ))
    db_session.commit()
    resp = client.get("/api/dashboard/stats")
    assert resp.json()["best_streak"] >= 12


# ── GET /api/dashboard/textbook/{textbook} ────────────────────────────

def test_textbook_detail_empty(client):
    resp = client.get("/api/dashboard/textbook/Voca_8000")
    assert resp.status_code == 200
    body = resp.json()
    assert body["textbook"] == "Voca_8000"
    assert body["lessons"] == []


def test_textbook_detail_lists_lessons(client, db_session):
    _seed_study_items(db_session, textbook="Voca_8000", lesson="Lesson_01", n=2)
    _seed_study_items(db_session, textbook="Voca_8000", lesson="Lesson_02", n=4)
    resp = client.get("/api/dashboard/textbook/Voca_8000")
    body = resp.json()
    assert len(body["lessons"]) == 2
    by_lesson = {l["lesson"]: l["words"] for l in body["lessons"]}
    assert by_lesson["Lesson_01"] == 2
    assert by_lesson["Lesson_02"] == 4


def test_textbook_detail_unknown_textbook_empty(client):
    resp = client.get("/api/dashboard/textbook/Nonexistent")
    assert resp.status_code == 200
    assert resp.json()["lessons"] == []


# ── GET /api/dashboard/analytics ──────────────────────────────────────

def test_analytics_empty(client):
    resp = client.get("/api/dashboard/analytics")
    assert resp.status_code == 200
    body = resp.json()
    for key in ("recent_activity", "weak_words", "stage_stats",
                "lesson_progress", "total_study_sec", "today_study_sec",
                "study_streak_days"):
        assert key in body
    assert body["total_study_sec"] == 0
    assert body["study_streak_days"] == 0


def test_analytics_lists_are_typed(client):
    """Empty DB → all analytics list fields are lists, not None."""
    body = client.get("/api/dashboard/analytics").json()
    for key in ("recent_activity", "weak_words", "stage_stats", "lesson_progress"):
        assert isinstance(body[key], list)
