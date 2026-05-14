"""Tests for backend/routers/day_off.py — child-side day-off requests.

Covers the list endpoint and the create endpoint (date validation,
duplicate-date 409, pending status, email-queue best-effort flag).
No parent_email is configured on the test host, so email_queued is
False and no email send is attempted.
"""

import pytest


@pytest.fixture(autouse=True)
def _clean_day_off(db_session):
    """Wipe DayOffRequest rows before/after each test (StaticPool persistence)."""
    from backend.models import DayOffRequest
    db_session.query(DayOffRequest).delete()
    db_session.commit()
    yield
    db_session.query(DayOffRequest).delete()
    db_session.commit()


# ── GET /api/day-off/requests ─────────────────────────────────────────

def test_list_empty(client):
    resp = client.get("/api/day-off/requests")
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 0
    assert body["requests"] == []


# ── POST /api/day-off/request ─────────────────────────────────────────

def test_create_request(client):
    resp = client.post("/api/day-off/request", json={
        "request_date": "2026-06-15",
        "reason": "Family trip to the mountains.",
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["id"] > 0
    assert body["request_date"] == "2026-06-15"
    assert body["status"] == "pending"
    assert body["parent_response"] is None
    # No PARENT_EMAIL configured on test host → email not queued
    assert body["email_queued"] is False


def test_create_bad_date_400(client):
    resp = client.post("/api/day-off/request", json={
        "request_date": "15-06-2026", "reason": "bad date format",
    })
    assert resp.status_code == 400


def test_create_empty_reason_400(client):
    resp = client.post("/api/day-off/request", json={
        "request_date": "2026-06-15", "reason": "",
    })
    assert resp.status_code == 400


def test_create_duplicate_date_409(client):
    payload = {"request_date": "2026-07-01", "reason": "first request"}
    first = client.post("/api/day-off/request", json=payload)
    assert first.status_code == 201
    dup = client.post("/api/day-off/request", json={
        "request_date": "2026-07-01", "reason": "second request same date",
    })
    assert dup.status_code == 409


def test_create_then_list(client):
    client.post("/api/day-off/request", json={
        "request_date": "2026-08-01", "reason": "reason one",
    })
    client.post("/api/day-off/request", json={
        "request_date": "2026-08-02", "reason": "reason two",
    })
    resp = client.get("/api/day-off/requests")
    body = resp.json()
    assert body["count"] == 2
    # Ordered by request_date DESC
    dates = [r["request_date"] for r in body["requests"]]
    assert dates == ["2026-08-02", "2026-08-01"]
    for r in body["requests"]:
        assert r["status"] == "pending"
