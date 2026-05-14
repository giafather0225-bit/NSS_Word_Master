"""Tests for backend/routers/ai_coach.py — daily motivational message.

On the test host Ollama isn't running and GEMINI_API_KEY is unset, so
the endpoint falls through to the canned-message branch. These tests
verify it always returns a valid {"message": str} without raising.
"""

import pytest


@pytest.fixture(autouse=True)
def _clean_xp_tables(db_session):
    """Wipe XP/streak tables so get_total_xp / get_current_streak start at 0."""
    from backend.models import XPLog, StreakLog
    for m in (XPLog, StreakLog):
        db_session.query(m).delete()
    db_session.commit()
    yield
    for m in (XPLog, StreakLog):
        db_session.query(m).delete()
    db_session.commit()


# ── GET /api/ai-coach/today ───────────────────────────────────────────

def test_returns_message(client):
    """Endpoint always returns a non-empty message string."""
    resp = client.get("/api/ai-coach/today")
    assert resp.status_code == 200
    body = resp.json()
    assert "message" in body
    assert isinstance(body["message"], str)
    assert len(body["message"]) > 0


def test_canned_fallback_on_test_host(client):
    """With no Ollama/Gemini available, the message is one of the canned set."""
    from backend.routers.ai_coach import CANNED
    resp = client.get("/api/ai-coach/today")
    # On the test host the message should be a canned one (≤200 chars guard
    # in the router also keeps real responses bounded).
    assert resp.json()["message"] in CANNED


def test_message_length_bounded(client):
    """The router caps responses at <200 chars — verify the contract."""
    resp = client.get("/api/ai-coach/today")
    assert len(resp.json()["message"]) < 200


def test_works_with_seeded_xp(client, db_session):
    """Seeded XP/streak rows don't break the endpoint — stats just feed
    the prompt; the canned fallback still returns cleanly."""
    from datetime import datetime, date
    from backend.models import XPLog
    db_session.add(XPLog(action="stage_complete", xp_amount=50, detail="",
                         earned_date=date.today().isoformat(),
                         created_at=datetime.now().isoformat()))
    db_session.commit()
    resp = client.get("/api/ai-coach/today")
    assert resp.status_code == 200
    assert len(resp.json()["message"]) > 0
