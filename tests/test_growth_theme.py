"""Tests for backend/routers/growth_theme.py — Growth Theme progression.

Covers the active-theme query, the all-themes listing, theme selection
(validation + activation/deactivation), and XP-driven step advance.
"""

import pytest


@pytest.fixture(autouse=True)
def _clean_growth_tables(db_session):
    """Wipe growth-theme tables before/after each test (StaticPool persistence)."""
    from backend.models import XPLog
    from backend.models.gamification import GrowthThemeProgress
    from backend.models import GrowthEvent
    for m in (GrowthThemeProgress, GrowthEvent, XPLog):
        db_session.query(m).delete()
    db_session.commit()
    yield
    for m in (GrowthThemeProgress, GrowthEvent, XPLog):
        db_session.query(m).delete()
    db_session.commit()


def _grant_xp(db, amount):
    from datetime import datetime
    from backend.models import XPLog
    db.add(XPLog(action="stage_complete", xp_amount=amount, detail="",
                 earned_date=datetime.now().date().isoformat(),
                 created_at=datetime.now().isoformat()))
    db.commit()


# ── GET /api/growth/theme ─────────────────────────────────────────────

def test_active_theme_none_initially(client):
    resp = client.get("/api/growth/theme")
    assert resp.status_code == 200
    body = resp.json()
    assert body["active"] is None
    assert body["total_xp"] == 0
    assert "xp_thresholds" in body
    assert "themes" in body


# ── GET /api/growth/theme/all ─────────────────────────────────────────

def test_all_themes_lists_five(client):
    """All 5 catalog themes are returned even with no progress rows."""
    resp = client.get("/api/growth/theme/all")
    assert resp.status_code == 200
    themes = resp.json()["themes"]
    names = {t["theme"] for t in themes}
    assert names == {"space", "tree", "city", "animal", "ocean"}
    for t in themes:
        assert t["current_step"] == 0
        assert t["is_active"] is False


# ── POST /api/growth/theme/select ─────────────────────────────────────

def test_select_unknown_theme_400(client):
    resp = client.post("/api/growth/theme/select", json={"theme": "bogus"})
    assert resp.status_code == 400


def test_select_bad_variation_400(client):
    resp = client.post("/api/growth/theme/select",
                       json={"theme": "ocean", "variation": 9})
    assert resp.status_code == 400


def test_select_theme_activates(client):
    resp = client.post("/api/growth/theme/select",
                       json={"theme": "ocean", "variation": 2})
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert body["theme"]["theme"] == "ocean"
    assert body["theme"]["variation"] == 2
    assert body["theme"]["is_active"] is True

    # Now the active-theme endpoint reflects it
    active = client.get("/api/growth/theme").json()["active"]
    assert active is not None
    assert active["theme"] == "ocean"


def test_select_switches_active_theme(client):
    """Selecting a second theme deactivates the first."""
    client.post("/api/growth/theme/select", json={"theme": "ocean"})
    client.post("/api/growth/theme/select", json={"theme": "tree"})
    all_themes = client.get("/api/growth/theme/all").json()["themes"]
    active = [t for t in all_themes if t["is_active"]]
    assert len(active) == 1
    assert active[0]["theme"] == "tree"


# ── POST /api/growth/theme/advance ────────────────────────────────────

def test_advance_no_active_theme_404(client):
    resp = client.post("/api/growth/theme/advance")
    assert resp.status_code == 404


def test_advance_steps_up_with_xp(client, db_session):
    """With 350 XP (≥ threshold[2]=300) the active theme advances to step 2."""
    client.post("/api/growth/theme/select", json={"theme": "space"})
    _grant_xp(db_session, 350)
    resp = client.post("/api/growth/theme/advance")
    assert resp.status_code == 200
    # Active theme is now at step 2 (thresholds [0,100,300,600,...])
    active = client.get("/api/growth/theme").json()["active"]
    assert active["current_step"] == 2


def test_advance_no_xp_stays_at_step_zero(client):
    """Zero XP → advance keeps the theme at step 0."""
    client.post("/api/growth/theme/select", json={"theme": "city"})
    client.post("/api/growth/theme/advance")
    active = client.get("/api/growth/theme").json()["active"]
    assert active["current_step"] == 0
