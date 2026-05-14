"""Tests for routers/lessons.py — subject/textbook/lesson directory + lookup.

Filesystem-listing endpoints are exercised only for their validation /
404 paths; the DB-backed /api/lesson-lookup is covered in full.
lessons.py is DUX-protected (CLAUDE.md rule 14) — tests are additive only.
"""
import pytest

from backend.models import Lesson, StudyItem


@pytest.fixture(autouse=True)
def _clean_tables(db_session):
    def _wipe():
        db_session.query(StudyItem).delete()
        db_session.query(Lesson).delete()
        db_session.commit()
    _wipe()
    yield
    _wipe()


# ── GET /api/subjects ─────────────────────────────────────────

def test_subjects_returns_list(client):
    r = client.get("/api/subjects")
    assert r.status_code == 200
    assert "subjects" in r.json()


# ── GET /api/textbooks/{subject} ──────────────────────────────

def test_textbooks_invalid_subject_name_400(client):
    # '!' is not allowed by _validate_name → 400
    assert client.get("/api/textbooks/bad!name").status_code == 400


def test_textbooks_unknown_subject_404(client):
    assert client.get("/api/textbooks/Nonexistent").status_code == 404


# ── GET /api/lessons/{subject}/{textbook} ─────────────────────

def test_lessons_by_textbook_unknown_404(client):
    assert client.get("/api/lessons/English/NoSuchBook").status_code == 404


# ── GET /api/lesson-lookup ────────────────────────────────────

def test_lesson_lookup_creates_row(client, db_session):
    r = client.get("/api/lesson-lookup",
                   params={"subject": "English", "textbook": "Voca_8000",
                           "lesson": "Lesson_99"})
    assert r.status_code == 200
    body = r.json()
    assert body["id"] > 0
    assert body["lesson_name"] == "Lesson_99"
    assert db_session.query(Lesson).count() == 1


def test_lesson_lookup_idempotent(client, db_session):
    params = {"subject": "English", "textbook": "Voca_8000", "lesson": "Lesson_99"}
    first = client.get("/api/lesson-lookup", params=params).json()
    second = client.get("/api/lesson-lookup", params=params).json()
    assert first["id"] == second["id"]
    assert db_session.query(Lesson).count() == 1


def test_lesson_lookup_numeric_lesson_normalized(client):
    body = client.get("/api/lesson-lookup",
                      params={"subject": "English", "textbook": "Voca_8000",
                              "lesson": "5"}).json()
    assert body["lesson_name"] == "Lesson_05"


def test_lesson_lookup_invalid_subject_400(client):
    r = client.get("/api/lesson-lookup",
                   params={"subject": "bad!subject", "textbook": "x",
                           "lesson": "Lesson_01"})
    assert r.status_code == 400
