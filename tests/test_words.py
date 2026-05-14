"""Tests for routers/words.py — Word CRUD + My Words weekly test.

Only DB-backed endpoints are covered here; the My_Words filesystem
endpoints (create/rename/delete lesson folders) are intentionally skipped
to avoid touching the real LEARNING_ROOT on disk.
"""
import pytest

from backend.models import Lesson, StudyItem, Word, GrowthEvent, XPLog


@pytest.fixture(autouse=True)
def _clean_tables(db_session):
    def _wipe():
        for model in (Word, StudyItem, GrowthEvent, XPLog, Lesson):
            db_session.query(model).delete()
        db_session.commit()
    _wipe()
    yield
    _wipe()


@pytest.fixture
def lesson(db_session):
    from datetime import datetime, timezone
    l = Lesson(subject="English", textbook="Voca_8000", lesson_name="Lesson_01",
               source_type="manual", description="",
               created_at=datetime.now(timezone.utc).isoformat())
    db_session.add(l)
    db_session.commit()
    db_session.refresh(l)
    return l


# ── POST /api/words/lesson/{id} ───────────────────────────────

def test_create_word_404_missing_lesson(client):
    r = client.post("/api/words/lesson/9999",
                    json={"word": "apple", "definition": "a fruit"})
    assert r.status_code == 404


def test_create_word_success(client, lesson, db_session):
    r = client.post(f"/api/words/lesson/{lesson.id}",
                    json={"word": "apple", "definition": "a round fruit",
                          "example": "I ate an apple.", "pos": "noun"})
    assert r.status_code == 201
    body = r.json()
    assert body["word"] == "apple"
    assert body["id"] > 0
    # linked StudyItem created
    assert db_session.query(StudyItem).filter_by(answer="apple").count() == 1


def test_create_word_duplicate_409(client, lesson):
    payload = {"word": "apple", "definition": "a fruit"}
    client.post(f"/api/words/lesson/{lesson.id}", json=payload)
    r = client.post(f"/api/words/lesson/{lesson.id}", json=payload)
    assert r.status_code == 409


# ── PATCH /api/words/lesson/{id}/{word_id} ────────────────────

def test_update_word_404(client, lesson):
    r = client.patch(f"/api/words/lesson/{lesson.id}/9999",
                     json={"definition": "new"})
    assert r.status_code == 404


def test_update_word_syncs_study_item(client, lesson, db_session):
    wid = client.post(f"/api/words/lesson/{lesson.id}",
                      json={"word": "apple", "definition": "old"}).json()["id"]
    r = client.patch(f"/api/words/lesson/{lesson.id}/{wid}",
                     json={"definition": "updated def"})
    assert r.status_code == 200
    assert r.json()["definition"] == "updated def"
    item = db_session.query(StudyItem).filter_by(answer="apple").first()
    assert item.question == "updated def"


# ── DELETE /api/words/lesson/{id}/{word_id} ───────────────────

def test_delete_word_404(client, lesson):
    assert client.delete(f"/api/words/lesson/{lesson.id}/9999").status_code == 404


def test_delete_word_removes_study_item(client, lesson, db_session):
    wid = client.post(f"/api/words/lesson/{lesson.id}",
                      json={"word": "apple", "definition": "x"}).json()["id"]
    r = client.delete(f"/api/words/lesson/{lesson.id}/{wid}")
    assert r.status_code == 204
    assert db_session.query(Word).count() == 0
    assert db_session.query(StudyItem).count() == 0


# ── GET /api/storage/lessons/{id}/words ───────────────────────

def test_get_lesson_words_404(client):
    assert client.get("/api/storage/lessons/9999/words").status_code == 404


def test_get_lesson_words_lists(client, lesson):
    client.post(f"/api/words/lesson/{lesson.id}",
                json={"word": "apple", "definition": "x"})
    body = client.get(f"/api/storage/lessons/{lesson.id}/words").json()
    assert body["count"] == 1
    assert body["words"][0]["word"] == "apple"


# ── GET /api/mywords/weekly-test ──────────────────────────────

def test_mywords_weekly_test_gate_not_met(client):
    body = client.get("/api/mywords/weekly-test").json()
    assert body["available"] is False
    assert body["min_required"] == 50
    assert body["words"] == []


def test_mywords_weekly_test_available(client, db_session):
    for i in range(55):
        db_session.add(StudyItem(
            subject="English", textbook="My_Words", lesson="L1",
            question=f"def {i}", answer=f"word{i}", hint="", extra_data="{}"))
    db_session.commit()
    body = client.get("/api/mywords/weekly-test").json()
    assert body["available"] is True
    assert body["total_word_count"] == 55
    assert body["test_size"] == 20


# ── POST /api/mywords/weekly-test/result ──────────────────────

def test_mywords_result_invalid_total_400(client):
    r = client.post("/api/mywords/weekly-test/result",
                    json={"correct_count": 0, "total_count": 0})
    assert r.status_code == 400


def test_mywords_result_correct_out_of_range_400(client):
    r = client.post("/api/mywords/weekly-test/result",
                    json={"correct_count": 25, "total_count": 20})
    assert r.status_code == 400


def test_mywords_result_pass_awards_xp(client, db_session):
    r = client.post("/api/mywords/weekly-test/result",
                    json={"correct_count": 19, "total_count": 20})
    assert r.status_code == 200
    body = r.json()
    assert body["passed"] is True
    assert body["xp_awarded"] == 10
    assert db_session.query(GrowthEvent).count() == 1


def test_mywords_result_fail_no_xp(client):
    body = client.post("/api/mywords/weekly-test/result",
                       json={"correct_count": 10, "total_count": 20}).json()
    assert body["passed"] is False
    assert body["xp_awarded"] == 0
