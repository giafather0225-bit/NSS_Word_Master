"""Tests for routers/tutor_sentence.py — practice sentence storage + AI input validation.

The AI endpoints (/api/tutor, /api/evaluate-sentence) require live Ollama/
Gemini, so only their input-validation (422) paths are exercised here.
The DB-backed practice-sentence routes are covered in full.
"""
import pytest

from backend.models import UserPracticeSentence


@pytest.fixture(autouse=True)
def _clean_tables(db_session):
    db_session.query(UserPracticeSentence).delete()
    db_session.commit()
    yield
    db_session.query(UserPracticeSentence).delete()
    db_session.commit()


def _body(item_id=1, sentence="The cat is happy."):
    return {"subject": "English", "textbook": "Voca_8000",
            "lesson": "Lesson_01", "item_id": item_id, "sentence": sentence}


# ── POST /api/practice/sentence ───────────────────────────────

def test_save_practice_sentence(client, db_session):
    r = client.post("/api/practice/sentence", json=_body())
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "saved"
    assert body["id"] > 0
    assert db_session.query(UserPracticeSentence).count() == 1


def test_save_practice_sentence_upserts_by_item(client, db_session):
    first = client.post("/api/practice/sentence",
                        json=_body(1, "First version.")).json()
    second = client.post("/api/practice/sentence",
                         json=_body(1, "Revised version.")).json()
    assert second["status"] == "updated"
    assert second["id"] == first["id"]
    assert db_session.query(UserPracticeSentence).count() == 1
    row = db_session.query(UserPracticeSentence).first()
    assert row.sentence == "Revised version."


def test_save_practice_sentence_too_long_422(client):
    r = client.post("/api/practice/sentence", json=_body(1, "x" * 600))
    assert r.status_code == 422


# ── GET /api/practice/sentences/{subject}/{textbook}/{lesson} ──

def test_list_practice_sentences_empty(client):
    body = client.get(
        "/api/practice/sentences/English/Voca_8000/Lesson_01").json()
    assert body == {"by_item_id": {}}


def test_list_practice_sentences_latest_per_item(client):
    client.post("/api/practice/sentence", json=_body(1, "Item 1 old."))
    client.post("/api/practice/sentence", json=_body(1, "Item 1 new."))
    client.post("/api/practice/sentence", json=_body(2, "Item 2 only."))
    body = client.get(
        "/api/practice/sentences/English/Voca_8000/Lesson_01").json()
    assert body["by_item_id"] == {"1": "Item 1 new.", "2": "Item 2 only."}


# ── POST /api/tutor — input validation ────────────────────────

def test_tutor_request_word_too_long_422(client):
    # Str80 word cap — fails validation before any network call.
    r = client.post("/api/tutor", json={"word": "x" * 200, "sentence": "hi"})
    assert r.status_code == 422
