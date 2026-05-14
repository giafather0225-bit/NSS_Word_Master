"""Tests for backend/routers/reward_shop.py — XP reward shop.

Covers the item catalog (auto-seeded), the atomic buy flow (XP balance
check + purchase row), my-rewards listing, PIN-gated use-reward, equip,
and PIN status/setup.

The shop PIN falls back to DEFAULT_PIN "0000" when no `pin` AppConfig
row exists — tests use that for the use-reward happy path.
"""

from datetime import datetime

import pytest


@pytest.fixture(autouse=True)
def _clean_shop_tables(db_session):
    """Wipe shop-related tables before/after each test.

    The StaticPool in-memory DB persists committed rows across the
    session — without this, seeded RewardItem/PurchasedReward/XPLog rows
    and the `pin` AppConfig row leak between tests.
    """
    from backend.models import RewardItem, PurchasedReward, XPLog, AppConfig
    def _wipe():
        for model in (RewardItem, PurchasedReward, XPLog):
            db_session.query(model).delete()
        db_session.query(AppConfig).filter(AppConfig.key == "pin").delete()
        db_session.commit()
    _wipe()
    yield
    _wipe()


def _grant_xp(db, amount):
    """Seed a positive XPLog row so the shop balance check passes."""
    from backend.models import XPLog
    db.add(XPLog(action="stage_complete", xp_amount=amount, detail="",
                 earned_date=datetime.now().date().isoformat(),
                 created_at=datetime.now().isoformat()))
    db.commit()


# ── GET /api/shop/items ───────────────────────────────────────────────

def test_items_auto_seeds(client):
    """First call seeds the 12 default reward items."""
    resp = client.get("/api/shop/items")
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body and "total_xp" in body
    assert len(body["items"]) == 12
    # Each item has the documented shape
    for it in body["items"]:
        for key in ("id", "name", "category", "price", "final_price", "is_active"):
            assert key in it


def test_items_category_filter(client):
    """?category= narrows the catalog."""
    client.get("/api/shop/items")  # seed
    resp = client.get("/api/shop/items?category=badge")
    assert resp.status_code == 200
    cats = {it["category"] for it in resp.json()["items"]}
    assert cats == {"badge"}


def test_items_total_xp_zero_initially(client):
    assert client.get("/api/shop/items").json()["total_xp"] == 0


# ── POST /api/shop/buy ────────────────────────────────────────────────

def test_buy_unknown_item_404(client):
    client.get("/api/shop/items")  # seed
    resp = client.post("/api/shop/buy", json={"item_id": 999999})
    assert resp.status_code == 404


def test_buy_not_enough_xp_400(client):
    items = client.get("/api/shop/items").json()["items"]
    cheapest = min(items, key=lambda i: i["final_price"])
    # No XP granted → balance 0 < price
    resp = client.post("/api/shop/buy", json={"item_id": cheapest["id"]})
    assert resp.status_code == 400


def test_buy_success_deducts_xp(client, db_session):
    items = client.get("/api/shop/items").json()["items"]
    cheapest = min(items, key=lambda i: i["final_price"])
    _grant_xp(db_session, cheapest["final_price"] + 100)

    resp = client.post("/api/shop/buy", json={"item_id": cheapest["id"]})
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert body["purchase_id"] > 0
    assert body["xp_spent"] == cheapest["final_price"]
    # Balance dropped by exactly the price
    assert body["remaining_xp"] == 100


def test_buy_creates_purchase_row(client, db_session):
    items = client.get("/api/shop/items").json()["items"]
    cheapest = min(items, key=lambda i: i["final_price"])
    _grant_xp(db_session, cheapest["final_price"] + 50)
    client.post("/api/shop/buy", json={"item_id": cheapest["id"]})

    rewards = client.get("/api/shop/my-rewards").json()["rewards"]
    assert len(rewards) == 1
    assert rewards[0]["is_used"] is False


# ── GET /api/shop/my-rewards ──────────────────────────────────────────

def test_my_rewards_empty(client):
    resp = client.get("/api/shop/my-rewards")
    assert resp.status_code == 200
    body = resp.json()
    assert body["rewards"] == []
    assert body["total_xp"] == 0


# ── POST /api/shop/use-reward/{id} ────────────────────────────────────

def test_use_reward_not_found_404(client):
    resp = client.post("/api/shop/use-reward/999999", json={"pin": "0000"})
    assert resp.status_code == 404


def test_use_reward_wrong_pin_403(client, db_session):
    items = client.get("/api/shop/items").json()["items"]
    cheapest = min(items, key=lambda i: i["final_price"])
    _grant_xp(db_session, cheapest["final_price"] + 10)
    pid = client.post("/api/shop/buy", json={"item_id": cheapest["id"]}).json()["purchase_id"]

    resp = client.post(f"/api/shop/use-reward/{pid}", json={"pin": "9999"})
    assert resp.status_code == 403


def test_use_reward_success_with_default_pin(client, db_session):
    items = client.get("/api/shop/items").json()["items"]
    cheapest = min(items, key=lambda i: i["final_price"])
    _grant_xp(db_session, cheapest["final_price"] + 10)
    pid = client.post("/api/shop/buy", json={"item_id": cheapest["id"]}).json()["purchase_id"]

    resp = client.post(f"/api/shop/use-reward/{pid}", json={"pin": "0000"})
    assert resp.status_code == 200
    assert resp.json()["ok"] is True

    # Second use rejected — already consumed
    again = client.post(f"/api/shop/use-reward/{pid}", json={"pin": "0000"})
    assert again.status_code == 400


# ── POST /api/shop/equip/{id} ─────────────────────────────────────────

def test_equip_not_found_404(client):
    resp = client.post("/api/shop/equip/999999", json={"equip": True})
    assert resp.status_code == 404


def test_equip_success(client, db_session):
    items = client.get("/api/shop/items").json()["items"]
    badge = next(i for i in items if i["category"] == "badge")
    _grant_xp(db_session, badge["final_price"] + 10)
    pid = client.post("/api/shop/buy", json={"item_id": badge["id"]}).json()["purchase_id"]

    resp = client.post(f"/api/shop/equip/{pid}", json={"equip": True})
    assert resp.status_code == 200
    assert resp.json()["is_equipped"] is True


# ── GET /api/shop/pin-status ──────────────────────────────────────────

def test_pin_status_not_set(client):
    """No `pin` row → pin_set is False."""
    resp = client.get("/api/shop/pin-status")
    assert resp.status_code == 200
    assert resp.json()["pin_set"] is False


# ── POST /api/shop/set-pin ────────────────────────────────────────────

def test_set_pin_invalid_format_400(client):
    resp = client.post("/api/shop/set-pin",
                       json={"pin": "12", "current_pin": "0000"})
    assert resp.status_code == 400


def test_set_pin_wrong_current_403(client):
    resp = client.post("/api/shop/set-pin",
                       json={"pin": "1234", "current_pin": "9999"})
    assert resp.status_code == 403


def test_set_pin_success_then_status(client):
    """Set a fresh PIN with the default current PIN, status flips to True."""
    resp = client.post("/api/shop/set-pin",
                       json={"pin": "1357", "current_pin": "0000"})
    assert resp.status_code == 200
    assert client.get("/api/shop/pin-status").json()["pin_set"] is True
