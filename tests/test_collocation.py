"""Tests for routers/collocation.py — daily collocation bonus stage.

Covers GET /api/collocation/today and POST /api/collocation/submit.
"""
from datetime import date

import pytest

from backend.models import XPLog, DailyWordsProgress


@pytest.fixture(autouse=True)
def _clean_tables(db_session):
    def _wipe():
        db_session.query(XPLog).delete()
        db_session.query(DailyWordsProgress).delete()
        db_session.commit()
    _wipe()
    yield
    _wipe()


def _answer(word, correct):
    return {
        "word": word,
        "collocation": f"{word} thing",
        "user_answer": "ans" if correct else "wrong",
        "correct": correct,
    }


# ── GET /today ────────────────────────────────────────────────

def test_today_default_grade_no_progress(client):
    r = client.get("/api/collocation/today")
    assert r.status_code == 200
    body = r.json()
    assert body["grade"] == "grade_4"
    assert body["total"] == len(body["items"])
    assert body["total"] <= 5


def test_today_grade_param_when_no_progress(client):
    body = client.get("/api/collocation/today?grade=5").json()
    assert body["grade"] == "grade_5"


def test_today_uses_progress_grade(client, db_session):
    db_session.add(DailyWordsProgress(
        grade="grade_3", cycle_start=date.today().isoformat(),
        word_index=0, test_words_json="[]", daily_learned=0,
    ))
    db_session.commit()
    body = client.get("/api/collocation/today").json()
    assert body["grade"] == "grade_3"


# ── POST /submit ──────────────────────────────────────────────

def test_submit_xp_per_correct(client):
    body = {"grade": 4, "answers": [_answer("a", True), _answer("b", True),
                                    _answer("c", False)]}
    r = client.post("/api/collocation/submit", json=body)
    assert r.status_code == 200
    data = r.json()
    assert data["correct_count"] == 2
    assert data["total"] == 3
    assert data["xp_earned"] == 6  # 2 * 3
    assert data["perfect"] is False


def test_submit_perfect_bonus(client):
    body = {"grade": 4, "answers": [_answer(c, True) for c in "abc"]}
    data = client.post("/api/collocation/submit", json=body).json()
    assert data["perfect"] is True
    assert data["xp_earned"] == 3 * 3 + 5  # per-correct + perfect bonus


def test_submit_perfect_bonus_deduped_per_day(client):
    body = {"grade": 4, "answers": [_answer(c, True) for c in "abc"]}
    first = client.post("/api/collocation/submit", json=body).json()
    second = client.post("/api/collocation/submit", json=body).json()
    assert first["xp_earned"] == 14
    assert second["xp_earned"] == 9  # per-correct only, perfect bonus deduped


def test_submit_empty_answers(client):
    data = client.post("/api/collocation/submit",
                       json={"grade": 4, "answers": []}).json()
    assert data["total"] == 0
    assert data["perfect"] is False
    assert data["xp_earned"] == 0


def test_submit_caps_at_max_items(client):
    body = {"grade": 4, "answers": [_answer(str(i), True) for i in range(7)]}
    data = client.post("/api/collocation/submit", json=body).json()
    assert data["total"] == 5  # sanitize() caps at MAX_ITEMS
