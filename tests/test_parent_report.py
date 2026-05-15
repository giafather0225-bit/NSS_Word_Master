"""Tests for routers/parent_report.py — weekly parent report API.

All four endpoints are PIN-gated (X-Parent-Pin header; DEFAULT_PIN "0000"
when no `pin` AppConfig row exists). The actual email-send path is not
exercised (no SMTP in tests) — only its 403/400 guards.
"""
import pytest

from backend.models import AppConfig

PIN = {"X-Parent-Pin": "0000"}


@pytest.fixture(autouse=True)
def _clean_tables(db_session):
    db_session.query(AppConfig).delete()
    db_session.commit()
    yield
    db_session.query(AppConfig).delete()
    db_session.commit()


# ── POST /api/parent/report/send ──────────────────────────────

def test_send_requires_pin(client):
    assert client.post("/api/parent/report/send").status_code == 403


def test_send_without_email_configured_400(client):
    r = client.post("/api/parent/report/send", headers=PIN)
    assert r.status_code == 400


# ── GET /api/parent/report/preview ────────────────────────────

def test_preview_requires_pin(client):
    assert client.get("/api/parent/report/preview").status_code == 403


def test_preview_returns_data_with_pin(client):
    r = client.get("/api/parent/report/preview", headers=PIN)
    assert r.status_code == 200
    assert isinstance(r.json(), dict)


# ── GET /api/parent/report/schedule ───────────────────────────

def test_get_schedule_requires_pin(client):
    assert client.get("/api/parent/report/schedule").status_code == 403


def test_get_schedule_defaults(client):
    body = client.get("/api/parent/report/schedule", headers=PIN).json()
    assert body["enabled"] is False
    assert body["day_of_week"] == 1
    assert body["child_name"] == "Gia"


# ── POST /api/parent/report/schedule ──────────────────────────

def test_set_schedule_requires_pin(client):
    r = client.post("/api/parent/report/schedule",
                    json={"enabled": True, "day_of_week": 3})
    assert r.status_code == 403


def test_set_schedule_success(client):
    r = client.post("/api/parent/report/schedule",
                    json={"enabled": True, "day_of_week": 4, "child_name": "Gia"},
                    headers=PIN)
    assert r.status_code == 200
    body = client.get("/api/parent/report/schedule", headers=PIN).json()
    assert body["enabled"] is True
    assert body["day_of_week"] == 4


def test_set_schedule_invalid_day_400(client):
    r = client.post("/api/parent/report/schedule",
                    json={"enabled": True, "day_of_week": 9}, headers=PIN)
    assert r.status_code == 400


def test_set_schedule_empty_child_name_400(client):
    r = client.post("/api/parent/report/schedule",
                    json={"enabled": True, "day_of_week": 1, "child_name": "   "},
                    headers=PIN)
    assert r.status_code == 400
