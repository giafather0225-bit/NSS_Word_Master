"""Tests for backend/routers/schedules.py — parent-set test schedule CRUD.

Covers list / create (date validation) / delete.
"""

import pytest


@pytest.fixture(autouse=True)
def _clean_schedules(db_session):
    """Wipe Schedule rows before/after each test (StaticPool persistence)."""
    from backend.models import Schedule
    db_session.query(Schedule).delete()
    db_session.commit()
    yield
    db_session.query(Schedule).delete()
    db_session.commit()


# ── GET /api/schedules ────────────────────────────────────────────────

def test_list_empty(client):
    resp = client.get("/api/schedules")
    assert resp.status_code == 200
    assert resp.json() == []


# ── POST /api/schedules ───────────────────────────────────────────────

def test_create_schedule(client):
    resp = client.post("/api/schedules", json={
        "test_date": "2026-09-15", "memo": "Unit 3 vocab test",
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] > 0
    assert body["test_date"] == "2026-09-15"
    assert body["memo"] == "Unit 3 vocab test"


def test_create_bad_date_400(client):
    resp = client.post("/api/schedules", json={
        "test_date": "09/15/2026", "memo": "bad format",
    })
    assert resp.status_code == 400


def test_create_then_list_newest_first(client):
    client.post("/api/schedules", json={"test_date": "2026-01-01", "memo": "first"})
    client.post("/api/schedules", json={"test_date": "2026-02-01", "memo": "second"})
    resp = client.get("/api/schedules")
    body = resp.json()
    assert len(body) == 2
    # Ordered by id DESC → "second" created last comes first
    assert body[0]["memo"] == "second"
    assert body[1]["memo"] == "first"


# ── DELETE /api/schedules/{id} ────────────────────────────────────────

def test_delete_schedule(client):
    created = client.post("/api/schedules", json={
        "test_date": "2026-03-10", "memo": "to delete",
    }).json()
    resp = client.delete(f"/api/schedules/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"
    assert client.get("/api/schedules").json() == []


def test_delete_nonexistent_is_idempotent(client):
    """Deleting a missing id is a no-op success (no 404)."""
    resp = client.delete("/api/schedules/999999")
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"
