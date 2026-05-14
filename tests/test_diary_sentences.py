"""Tests for backend/routers/diary_sentences.py — "My Sentences" view.

Covers GET /api/diary/{subject}/{textbook}: empty result shape, grouping
by lesson, the "all" textbook sentinel, and the StudyItem outer-join
(sentences whose item_id has no StudyItem still appear with word="").
"""

import pytest


@pytest.fixture(autouse=True)
def _clean_sentence_tables(db_session):
    """Wipe sentence-source tables before/after each test (StaticPool persistence)."""
    from backend.models import UserPracticeSentence, StudyItem
    for m in (UserPracticeSentence, StudyItem):
        db_session.query(m).delete()
    db_session.commit()
    yield
    for m in (UserPracticeSentence, StudyItem):
        db_session.query(m).delete()
    db_session.commit()


def _seed_sentence(db, lesson="Lesson_01", sentence="I like apples.",
                   item_id=None, subject="English", textbook="Voca_8000"):
    from backend.models import UserPracticeSentence
    row = UserPracticeSentence(
        subject=subject, textbook=textbook, lesson=lesson,
        item_id=item_id, sentence=sentence, created_at="",
    )
    db.add(row)
    db.commit()
    return row


# ── GET /api/diary/{subject}/{textbook} ───────────────────────────────

def test_empty_result(client):
    resp = client.get("/api/diary/English/Voca_8000")
    assert resp.status_code == 200
    body = resp.json()
    assert body["lessons"] == []
    assert body["total_sentences"] == 0


def test_sentences_grouped_by_lesson(client, db_session):
    _seed_sentence(db_session, lesson="Lesson_01", sentence="Sentence A1")
    _seed_sentence(db_session, lesson="Lesson_01", sentence="Sentence A2")
    _seed_sentence(db_session, lesson="Lesson_02", sentence="Sentence B1")

    resp = client.get("/api/diary/English/Voca_8000")
    body = resp.json()
    assert body["total_sentences"] == 3
    by_lesson = {l["lesson"]: l["sentences"] for l in body["lessons"]}
    assert len(by_lesson["Lesson_01"]) == 2
    assert len(by_lesson["Lesson_02"]) == 1


def test_sentence_without_study_item_has_blank_word(client, db_session):
    """A sentence whose item_id points to no StudyItem still appears,
    with word="" (outer join)."""
    _seed_sentence(db_session, sentence="Orphan sentence", item_id=999999)
    resp = client.get("/api/diary/English/Voca_8000")
    body = resp.json()
    assert body["total_sentences"] == 1
    assert body["lessons"][0]["sentences"][0]["word"] == ""
    assert body["lessons"][0]["sentences"][0]["sentence"] == "Orphan sentence"


def test_sentence_word_resolved_from_study_item(client, db_session):
    """When item_id matches a StudyItem, its answer fills the word field."""
    from backend.models import StudyItem
    item = StudyItem(subject="English", textbook="Voca_8000", lesson="Lesson_01",
                     source_type="manual", question="a fruit", answer="apple")
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)
    _seed_sentence(db_session, lesson="Lesson_01", sentence="I ate an apple.",
                   item_id=item.id)

    resp = client.get("/api/diary/English/Voca_8000")
    sent = resp.json()["lessons"][0]["sentences"][0]
    assert sent["word"] == "apple"


def test_textbook_filter(client, db_session):
    """A different textbook's sentences are excluded by the path filter."""
    _seed_sentence(db_session, textbook="Voca_8000", sentence="in voca")
    _seed_sentence(db_session, textbook="Other_Book", sentence="in other")
    resp = client.get("/api/diary/English/Voca_8000")
    body = resp.json()
    assert body["total_sentences"] == 1
    assert body["lessons"][0]["sentences"][0]["sentence"] == "in voca"


def test_all_sentinel_returns_every_textbook(client, db_session):
    """textbook='all' is a sentinel meaning no textbook filter."""
    _seed_sentence(db_session, textbook="Voca_8000", sentence="in voca")
    _seed_sentence(db_session, textbook="Other_Book", sentence="in other")
    resp = client.get("/api/diary/English/all")
    body = resp.json()
    assert body["total_sentences"] == 2
