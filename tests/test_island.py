"""Smoke tests for backend/routers/island.py.

Covers read-only endpoints that must return a valid shape even when the
island system has no seeded data — the primary purpose is to detect router
wiring breaks, schema field drift, and accidental 500s on empty state.
"""

import pytest


# ── /api/island/status ────────────────────────────────────────────────

def test_island_status_shape_empty_db(client):
    """Status endpoint returns the documented shape on an empty DB."""
    resp = client.get("/api/island/status")
    assert resp.status_code == 200
    body = resp.json()
    # Required top-level keys per ISLAND_SPEC
    for key in ("island_on", "initialized", "currency",
                "zones", "active_characters", "completed_count"):
        assert key in body, f"missing key: {key}"
    assert isinstance(body["zones"], list)
    assert isinstance(body["active_characters"], list)
    assert body["completed_count"] == 0


def test_island_status_currency_keys(client):
    """Currency block carries lumi / legend_lumi balance fields."""
    resp = client.get("/api/island/status")
    cur = resp.json()["currency"]
    # le.get_balance returns at least these two
    assert "lumi" in cur or "balance" in cur


# ── /api/island/onboarding/status ─────────────────────────────────────

def test_onboarding_status_default_false(client):
    """Fresh DB → not initialized."""
    resp = client.get("/api/island/onboarding/status")
    assert resp.status_code == 200
    assert resp.json()["initialized"] is False


# ── /api/island/zone/status ───────────────────────────────────────────

def test_zone_status_returns_list(client):
    resp = client.get("/api/island/zone/status")
    assert resp.status_code == 200
    body = resp.json()
    assert "zones" in body
    assert isinstance(body["zones"], list)


# ── /api/island/currency ──────────────────────────────────────────────

def test_currency_endpoint(client):
    resp = client.get("/api/island/currency")
    assert resp.status_code == 200
    body = resp.json()
    # Either {lumi: N, legend_lumi: N} or {balance: N} shape — both acceptable
    assert isinstance(body, dict)
    assert len(body) > 0


def test_lumi_log_empty(client):
    resp = client.get("/api/island/lumi/log")
    assert resp.status_code == 200
    body = resp.json()
    assert "log" in body
    assert isinstance(body["log"], list)


# ── /api/island/characters ────────────────────────────────────────────

def test_characters_list(client):
    resp = client.get("/api/island/characters")
    assert resp.status_code == 200
    # Returns list of catalog characters (or wrapped dict)
    body = resp.json()
    assert isinstance(body, (list, dict))


def test_active_character_empty_db(client):
    """No adopted character → endpoint must not 500."""
    resp = client.get("/api/island/character/active")
    # Either 200 with null or 404 — both are valid "no active" responses
    assert resp.status_code in (200, 404)


# ── /api/island/shop ──────────────────────────────────────────────────

def test_shop_listing(client):
    resp = client.get("/api/island/shop")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, dict)
    # Either grouped by category or flat list of items
    assert "items" in body or "evolution" in body or "food" in body or "decor" in body


def test_inventory_empty(client):
    resp = client.get("/api/island/inventory")
    assert resp.status_code == 200


def test_placed_empty(client):
    resp = client.get("/api/island/placed")
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body or isinstance(body, list)


# ── /api/island/zone/unlock — validation ──────────────────────────────

def test_zone_unlock_unknown_zone_404(client):
    """Bogus zone name returns 404, not 500."""
    resp = client.post("/api/island/zone/unlock", json={"zone": "nonexistent_zone"})
    assert resp.status_code == 404


def test_zone_unlock_missing_body_422(client):
    resp = client.post("/api/island/zone/unlock", json={})
    assert resp.status_code == 422
