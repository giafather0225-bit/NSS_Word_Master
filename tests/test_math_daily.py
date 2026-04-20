"""Tests for backend/routers/math_daily.py."""
import pytest

from backend.models import (
    MathDailyChallenge,
    MathProgress,
    MathWrongReview,
    StreakLog,
    XPLog,
)


@pytest.fixture(autouse=True)
def _clean_daily_tables(db_session):
    models = (MathDailyChallenge, MathProgress, MathWrongReview, XPLog, StreakLog)
    for m in models:
        db_session.query(m).delete()
    db_session.commit()
    yield
    for m in models:
        db_session.query(m).delete()
    db_session.commit()


def test_today_creates_challenge(client):
    resp = client.get("/api/math/daily/today")
    assert resp.status_code == 200
    body = resp.json()
    assert body["exists"] is True
    assert body["completed"] is False
    assert len(body["problems"]) > 0
    # Answers should be stripped from client payload
    for p in body["problems"]:
        assert "answer" not in p
        assert "id" in p
        assert "question" in p


def test_today_is_idempotent(client):
    r1 = client.get("/api/math/daily/today").json()
    r2 = client.get("/api/math/daily/today").json()
    # Same set of problems across calls on the same date
    ids1 = [p["id"] for p in r1["problems"]]
    ids2 = [p["id"] for p in r2["problems"]]
    assert ids1 == ids2


def test_submit_answer_without_start_fails(client):
    resp = client.post(
        "/api/math/daily/submit-answer",
        json={"index": 0, "answer": "A"},
    )
    assert resp.status_code == 400


def test_submit_answer_invalid_index(client):
    client.get("/api/math/daily/today")
    resp = client.post(
        "/api/math/daily/submit-answer",
        json={"index": 999, "answer": "A"},
    )
    assert resp.status_code == 400


def test_submit_answer_scores_correctly(client):
    today = client.get("/api/math/daily/today").json()
    assert today["problems"], "need at least one problem"
    resp = client.post(
        "/api/math/daily/submit-answer",
        json={"index": 0, "answer": "definitely_not_right_zzz"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["is_correct"] is False
    assert "correct_answer" in body
    assert "feedback" in body


def test_complete_awards_xp(client, db_session):
    client.get("/api/math/daily/today")
    resp = client.post(
        "/api/math/daily/complete",
        json={"score": 5, "total": 5},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "completed"
    assert body["score"] == 5
    # Perfect score → 5 (complete) + 3 (perfect) = 8
    assert body["xp"] == 8
    row = db_session.query(MathDailyChallenge).first()
    assert row is not None
    assert row.completed is True
