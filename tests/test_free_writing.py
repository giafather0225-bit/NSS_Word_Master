"""Tests for backend/routers/free_writing.py — Diary Free Writing CRUD.

Covers list / create / delete. The create endpoint calls
_get_grammar_feedback (Ollama → Gemini → canned fallback); on the test
host with no Ollama/Gemini it falls back to the canned string, so no
network call fires and the endpoint still returns 201.
"""

import pytest


@pytest.fixture(autouse=True)
def _clean_free_writing(db_session):
    """Wipe FreeWriting rows before/after each test (StaticPool persistence)."""
    from backend.models import FreeWriting
    db_session.query(FreeWriting).delete()
    db_session.commit()
    yield
    db_session.query(FreeWriting).delete()
    db_session.commit()


# ── GET /api/free-writing/entries ─────────────────────────────────────

def test_list_empty(client):
    resp = client.get("/api/free-writing/entries")
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 0
    assert body["entries"] == []


# ── POST /api/free-writing/entries ────────────────────────────────────

def test_create_entry(client):
    resp = client.post("/api/free-writing/entries", json={
        "title": "My First Story",
        "content": "Once upon a time there was a curious fox.",
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["id"] > 0
    assert body["title"] == "My First Story"
    assert body["content"].startswith("Once upon a time")
    # ai_feedback is always populated (canned fallback when AI unavailable)
    assert body["ai_feedback"] is not None


def test_create_empty_title_400(client):
    resp = client.post("/api/free-writing/entries", json={
        "title": "", "content": "some content",
    })
    assert resp.status_code == 400


def test_create_empty_content_400(client):
    resp = client.post("/api/free-writing/entries", json={
        "title": "A Title", "content": "",
    })
    assert resp.status_code == 400


def test_create_then_list(client):
    client.post("/api/free-writing/entries", json={
        "title": "Entry A", "content": "content A",
    })
    client.post("/api/free-writing/entries", json={
        "title": "Entry B", "content": "content B",
    })
    resp = client.get("/api/free-writing/entries")
    body = resp.json()
    assert body["count"] == 2
    titles = {e["title"] for e in body["entries"]}
    assert titles == {"Entry A", "Entry B"}


# ── DELETE /api/free-writing/entries/{id} ─────────────────────────────

def test_delete_entry(client):
    created = client.post("/api/free-writing/entries", json={
        "title": "Delete Me", "content": "to be removed",
    }).json()
    resp = client.delete(f"/api/free-writing/entries/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["deleted"] == created["id"]
    # List is now empty
    assert client.get("/api/free-writing/entries").json()["count"] == 0


def test_delete_not_found_404(client):
    resp = client.delete("/api/free-writing/entries/999999")
    assert resp.status_code == 404
