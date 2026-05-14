"""Tests for backend/routers/starred.py — starred (favourited) study items.

Covers the star toggle (PATCH) and the starred-items listing (GET).
"""

import pytest


@pytest.fixture(autouse=True)
def _clean_study_items(db_session):
    """Wipe StudyItem rows before/after each test (StaticPool persistence)."""
    from backend.models import StudyItem
    db_session.query(StudyItem).delete()
    db_session.commit()
    yield
    db_session.query(StudyItem).delete()
    db_session.commit()


def _seed_item(db, answer="apple", question="a round fruit",
               lesson="Lesson_01", textbook="Voca_8000"):
    from backend.models import StudyItem
    item = StudyItem(subject="English", textbook=textbook, lesson=lesson,
                     source_type="manual", question=question, answer=answer,
                     hint="I ate an apple.")
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


# ── PATCH /api/study-items/{id}/star ──────────────────────────────────

def test_toggle_star_not_found_404(client):
    resp = client.patch("/api/study-items/999999/star")
    assert resp.status_code == 404


def test_toggle_star_on(client, db_session):
    item = _seed_item(db_session)
    resp = client.patch(f"/api/study-items/{item.id}/star")
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert body["is_starred"] is True
    assert body["item"]["word"] == "apple"
    assert body["item"]["meaning"] == "a round fruit"


def test_toggle_star_twice_returns_to_unstarred(client, db_session):
    item = _seed_item(db_session)
    client.patch(f"/api/study-items/{item.id}/star")          # → starred
    resp = client.patch(f"/api/study-items/{item.id}/star")   # → unstarred
    assert resp.status_code == 200
    assert resp.json()["is_starred"] is False


# ── GET /api/study-items/starred ──────────────────────────────────────

def test_list_starred_empty(client):
    resp = client.get("/api/study-items/starred")
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 0
    assert body["items"] == []


def test_list_starred_only_includes_starred(client, db_session):
    a = _seed_item(db_session, answer="alpha")
    b = _seed_item(db_session, answer="bravo")
    _seed_item(db_session, answer="charlie")  # left unstarred

    client.patch(f"/api/study-items/{a.id}/star")
    client.patch(f"/api/study-items/{b.id}/star")

    resp = client.get("/api/study-items/starred")
    body = resp.json()
    assert body["count"] == 2
    words = {it["word"] for it in body["items"]}
    assert words == {"alpha", "bravo"}
    for it in body["items"]:
        assert it["is_starred"] is True


def test_list_starred_excludes_after_unstar(client, db_session):
    item = _seed_item(db_session, answer="delta")
    client.patch(f"/api/study-items/{item.id}/star")
    assert client.get("/api/study-items/starred").json()["count"] == 1
    client.patch(f"/api/study-items/{item.id}/star")  # unstar
    assert client.get("/api/study-items/starred").json()["count"] == 0
