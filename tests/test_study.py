"""Tests for routers/study.py — study session data + learning analytics logs.

study.py is DUX-protected (CLAUDE.md rule 14) — tests are additive only.
"""
import pytest

from backend.models import StudyItem, Progress
from backend.models.learning import LearningLog, WordAttempt, AcademySession


@pytest.fixture(autouse=True)
def _clean_tables(db_session):
    def _wipe():
        for model in (StudyItem, Progress, LearningLog, WordAttempt, AcademySession):
            db_session.query(model).delete()
        db_session.commit()
    _wipe()
    yield
    _wipe()


def _seed_items(db, n=3):
    for i in range(n):
        db.add(StudyItem(
            subject="English", textbook="Voca_8000", lesson="Lesson_01",
            question=f"def {i}", answer=f"word{i}", hint="", extra_data="{}"))
    db.commit()


# ── GET /api/study/{subject}/{textbook}/{lesson} ──────────────

def test_study_empty_lesson(client):
    body = client.get("/api/study/English/Voca_8000/Lesson_88").json()
    assert body["items"] == []
    assert body["progress"]["current_index"] == 0


def test_study_with_items_creates_progress(client, db_session):
    _seed_items(db_session, 3)
    body = client.get("/api/study/English/Voca_8000/Lesson_01").json()
    assert len(body["items"]) == 3
    assert body["progress"]["current_index"] == 0
    assert db_session.query(Progress).count() == 1


def test_study_invalid_subject_name_400(client):
    assert client.get("/api/study/bad!subj/Voca_8000/Lesson_01").status_code == 400


# ── POST /api/learning/log ────────────────────────────────────

def test_learning_log_saved(client, db_session):
    r = client.post("/api/learning/log", json={
        "textbook": "Voca_8000", "lesson": "Lesson_01", "stage": "PREVIEW",
        "word_count": 10, "correct_count": 9, "duration_sec": 120,
    })
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert "island" in body
    assert db_session.query(LearningLog).count() == 1


def test_learning_log_clamps_negative_duration(client):
    r = client.post("/api/learning/log", json={
        "textbook": "Voca_8000", "lesson": "Lesson_01", "stage": "PREVIEW",
        "word_count": -5, "correct_count": -1, "duration_sec": -99,
    })
    assert r.status_code == 200
    assert r.json()["ok"] is True


# ── POST /api/learning/word-attempt ───────────────────────────

def test_word_attempt_saved(client, db_session):
    r = client.post("/api/learning/word-attempt", json={
        "textbook": "Voca_8000", "lesson": "Lesson_01", "word": "apple",
        "stage": "SPELLING", "is_correct": True, "user_answer": "apple",
    })
    assert r.status_code == 200
    assert r.json()["ok"] is True
    assert db_session.query(WordAttempt).count() == 1


# ── POST /api/learning/word-attempts-batch ────────────────────

def test_word_attempts_batch_saved(client, db_session):
    attempts = [
        {"textbook": "Voca_8000", "lesson": "Lesson_01", "word": f"w{i}",
         "stage": "WORD_MATCH", "is_correct": i % 2 == 0}
        for i in range(4)
    ]
    r = client.post("/api/learning/word-attempts-batch", json={"attempts": attempts})
    assert r.status_code == 200
    assert r.json()["count"] == 4
    assert db_session.query(WordAttempt).count() == 4


def test_word_attempts_batch_empty(client):
    r = client.post("/api/learning/word-attempts-batch", json={"attempts": []})
    assert r.status_code == 200
    assert r.json()["count"] == 0
