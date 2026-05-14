"""Tests for backend/routers/progress.py — answer verification + streak progress.

Covers sparta_reset, challenge_complete, and verify (correct/wrong streak
logic, 404 on missing data, 403 on lesson mismatch).

Note: progress.py is a DUX-protected file (CLAUDE.md rule 14) — these
tests are additive and never modify the router itself.
"""

import pytest


@pytest.fixture(autouse=True)
def _clean_progress_tables(db_session):
    """Wipe StudyItem + Progress before/after each test (StaticPool persistence)."""
    from backend.models import StudyItem, Progress
    for m in (StudyItem, Progress):
        db_session.query(m).delete()
    db_session.commit()
    yield
    for m in (StudyItem, Progress):
        db_session.query(m).delete()
    db_session.commit()


def _seed_item(db, answer="apple", lesson="Lesson_01",
               subject="English", textbook="Voca_8000"):
    from backend.models import StudyItem
    item = StudyItem(subject=subject, textbook=textbook, lesson=lesson,
                     source_type="manual", question="a fruit", answer=answer)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def _seed_progress(db, lesson="Lesson_01", current_index=0, best_streak=0,
                   subject="English", textbook="Voca_8000"):
    from backend.models import Progress
    p = Progress(subject=subject, textbook=textbook, lesson=lesson,
                 current_index=current_index, best_streak=best_streak)
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


_SL = {"subject": "English", "textbook": "Voca_8000", "lesson": "Lesson_01"}


# ── POST /api/progress/sparta_reset ───────────────────────────────────

def test_sparta_reset_no_progress_row(client):
    """Reset with no Progress row is a no-op success."""
    resp = client.post("/api/progress/sparta_reset", json=_SL)
    assert resp.status_code == 200
    assert resp.json()["status"] == "reset"


def test_sparta_reset_zeroes_index(client, db_session):
    _seed_progress(db_session, current_index=7, best_streak=10)
    resp = client.post("/api/progress/sparta_reset", json=_SL)
    assert resp.status_code == 200
    from backend.models import Progress
    p = db_session.query(Progress).filter_by(lesson="Lesson_01").first()
    assert p.current_index == 0
    assert p.best_streak == 10  # best_streak untouched


# ── POST /api/progress/challenge_complete ─────────────────────────────

def test_challenge_complete_creates_progress(client, db_session):
    """No existing Progress row → one is created, best_streak = item count."""
    _seed_item(db_session, answer="alpha")
    _seed_item(db_session, answer="bravo")
    resp = client.post("/api/progress/challenge_complete", json=_SL)
    assert resp.status_code == 200
    assert resp.json()["best_streak"] == 2


def test_challenge_complete_keeps_higher_best(client, db_session):
    """best_streak only grows — a smaller item count doesn't shrink it."""
    _seed_item(db_session, answer="solo")
    _seed_progress(db_session, best_streak=99)
    resp = client.post("/api/progress/challenge_complete", json=_SL)
    assert resp.json()["best_streak"] == 99


# ── POST /api/progress/verify ─────────────────────────────────────────

def test_verify_missing_data_404(client):
    resp = client.post("/api/progress/verify", json={
        **_SL, "item_id": 999999, "user_input": "x",
    })
    assert resp.status_code == 404


def test_verify_correct_advances_streak(client, db_session):
    item = _seed_item(db_session, answer="apple")
    _seed_progress(db_session, current_index=2, best_streak=2)
    resp = client.post("/api/progress/verify", json={
        **_SL, "item_id": item.id, "user_input": "apple",
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["is_correct"] is True
    assert body["current_index"] == 3
    assert body["best_streak"] == 3


def test_verify_wrong_resets_streak(client, db_session):
    item = _seed_item(db_session, answer="apple")
    _seed_progress(db_session, current_index=5, best_streak=8)
    resp = client.post("/api/progress/verify", json={
        **_SL, "item_id": item.id, "user_input": "banana",
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["is_correct"] is False
    assert body["current_index"] == 0
    assert body["best_streak"] == 8  # best_streak preserved


def test_verify_case_insensitive(client, db_session):
    item = _seed_item(db_session, answer="Apple")
    _seed_progress(db_session)
    resp = client.post("/api/progress/verify", json={
        **_SL, "item_id": item.id, "user_input": "  APPLE  ",
    })
    assert resp.json()["is_correct"] is True


def test_verify_lesson_mismatch_403(client, db_session):
    """An item that belongs to a different lesson → 403."""
    item = _seed_item(db_session, answer="apple", lesson="Lesson_99")
    _seed_progress(db_session, lesson="Lesson_01")
    resp = client.post("/api/progress/verify", json={
        **_SL, "item_id": item.id, "user_input": "apple",
    })
    assert resp.status_code == 403
