"""Tests for backend/routers/diary.py — diary entries + growth timeline.

Covers entry CRUD (create/update/get/delete), the list endpoint with
date filtering + pagination, and the growth timeline. AI grammar
feedback is opt-in (feedback_requested=False default) so these tests
never trigger an Ollama/Gemini call.
"""

from datetime import date


# ── GET /api/diary/entries ────────────────────────────────────────────

def test_list_entries_empty(client):
    resp = client.get("/api/diary/entries")
    assert resp.status_code == 200
    body = resp.json()
    for key in ("total", "count", "offset", "limit", "entries"):
        assert key in body
    assert body["entries"] == []


def test_list_entries_bad_date_400(client):
    resp = client.get("/api/diary/entries?date=not-a-date")
    assert resp.status_code == 400


# ── POST /api/diary/entries ───────────────────────────────────────────

def test_create_entry(client):
    resp = client.post("/api/diary/entries", json={
        "content": "Today I learned about spaced repetition.",
        "entry_date": "2026-05-10",
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["id"] > 0
    assert body["entry_date"] == "2026-05-10"
    assert body["content"].startswith("Today I learned")
    # feedback not requested → ai_feedback stays None
    assert body["ai_feedback"] is None


def test_create_entry_bad_date_400(client):
    resp = client.post("/api/diary/entries", json={
        "content": "x", "entry_date": "10-05-2026",
    })
    assert resp.status_code == 400


def test_create_entry_updates_existing_same_date_mode(client):
    """Posting twice for the same (date, mode) updates in place — one row."""
    client.post("/api/diary/entries", json={
        "content": "first version", "entry_date": "2026-05-11", "mode": "journal",
    })
    resp2 = client.post("/api/diary/entries", json={
        "content": "second version", "entry_date": "2026-05-11", "mode": "journal",
    })
    assert resp2.status_code == 201
    assert resp2.json()["content"] == "second version"

    # List for that date returns exactly one entry
    listing = client.get("/api/diary/entries?date=2026-05-11")
    assert listing.json()["total"] == 1


def test_create_entry_with_metadata(client):
    """Title / mood / style metadata round-trips through create + read."""
    resp = client.post("/api/diary/entries", json={
        "content": "A decorated entry.",
        "entry_date": "2026-05-12",
        "title": "My Day",
        "mood": "happy",
        "mode": "journal",
        "style": {"paper": "lined", "fill": "#FFFFFF"},
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == "My Day"
    assert body["mood"] == "happy"
    assert body["style"] == {"paper": "lined", "fill": "#FFFFFF"}


# ── GET /api/diary/entries/{id} ───────────────────────────────────────

def test_get_entry_by_id(client):
    created = client.post("/api/diary/entries", json={
        "content": "Fetch me by id.", "entry_date": "2026-05-13",
    }).json()
    resp = client.get(f"/api/diary/entries/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == created["id"]


def test_get_entry_not_found_404(client):
    resp = client.get("/api/diary/entries/999999")
    assert resp.status_code == 404


# ── DELETE /api/diary/entries/{id} ────────────────────────────────────

def test_delete_entry(client):
    created = client.post("/api/diary/entries", json={
        "content": "Delete me.", "entry_date": "2026-05-14",
    }).json()
    resp = client.delete(f"/api/diary/entries/{created['id']}")
    assert resp.status_code == 204
    # Now gone
    assert client.get(f"/api/diary/entries/{created['id']}").status_code == 404


def test_delete_entry_not_found_404(client):
    resp = client.delete("/api/diary/entries/999999")
    assert resp.status_code == 404


# ── Pagination + filtering ────────────────────────────────────────────

def test_list_pagination(client):
    """offset/limit paginate the entry list."""
    for i in range(5):
        client.post("/api/diary/entries", json={
            "content": f"entry {i}", "entry_date": f"2026-04-0{i+1}",
        })
    page = client.get("/api/diary/entries?limit=2&offset=0")
    assert page.status_code == 200
    body = page.json()
    assert body["count"] == 2
    assert body["total"] >= 5
    assert body["limit"] == 2


def test_list_date_filter(client):
    """?date= narrows the result to a single date."""
    client.post("/api/diary/entries", json={
        "content": "filtered entry", "entry_date": "2026-03-15",
    })
    resp = client.get("/api/diary/entries?date=2026-03-15")
    body = resp.json()
    assert body["total"] == 1
    assert body["entries"][0]["entry_date"] == "2026-03-15"


# ── GET /api/growth/timeline ──────────────────────────────────────────

def test_growth_timeline_empty(client):
    resp = client.get("/api/growth/timeline")
    assert resp.status_code == 200
    body = resp.json()
    assert "count" in body and "events" in body
    assert isinstance(body["events"], list)


def test_growth_timeline_returns_events(client, db_session):
    """Seeded GrowthEvent rows appear in the timeline newest-first."""
    from backend.models import GrowthEvent
    db_session.add_all([
        GrowthEvent(event_type="lesson_pass", title="Older",
                    detail="", event_date="2026-01-01", created_at="2026-01-01T00:00:00"),
        GrowthEvent(event_type="lesson_pass", title="Newer",
                    detail="", event_date="2026-05-01", created_at="2026-05-01T00:00:00"),
    ])
    db_session.commit()
    resp = client.get("/api/growth/timeline")
    body = resp.json()
    assert body["count"] >= 2
    titles = [e["title"] for e in body["events"]]
    # Newest-first ordering
    assert titles.index("Newer") < titles.index("Older")
