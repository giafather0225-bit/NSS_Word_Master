"""
routers/reward_shop.py — Reward Shop API
Section: System / Shop
Dependencies: models.py (RewardItem, PurchasedReward, AppConfig),
              services/xp_engine.py
API: GET /api/shop/items, POST /api/shop/buy,
     GET /api/shop/my-rewards, POST /api/shop/use-reward/{id},
     POST /api/shop/equip/{id},
     GET /api/shop/pin-status, POST /api/shop/set-pin
"""

import logging
import os
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

try:
    from ..database import get_db
    from ..models import AppConfig, PurchasedReward, RewardItem
    from ..services import xp_engine, pin_guard, pin_hash
except ImportError:
    from database import get_db
    from models import AppConfig, PurchasedReward, RewardItem
    from services import xp_engine, pin_guard, pin_hash

router = APIRouter()
logger = logging.getLogger(__name__)

# ─── Seed Data ───────────────────────────────────────────────

SEED_REWARDS = [
    {"name": "Word Explorer Badge",  "category": "badge", "price": 50,   "icon": "🔍", "description": "You explored 50 new words!"},
    {"name": "Streak Master Badge",  "category": "badge", "price": 100,  "icon": "🔥", "description": "7-day streak achieved!"},
    {"name": "Perfect Scorer Badge", "category": "badge", "price": 150,  "icon": "💯", "description": "100% on a Final Test!"},
    {"name": "Ocean Theme",          "category": "theme", "price": 200,  "icon": "🌊", "description": "Cool ocean colors for your app"},
    {"name": "Space Theme",          "category": "theme", "price": 200,  "icon": "🚀", "description": "Dark space theme with stars"},
    {"name": "Forest Theme",         "category": "theme", "price": 200,  "icon": "🌲", "description": "Calm forest green theme"},
    {"name": "Hint Power",           "category": "power", "price": 30,   "icon": "💡", "description": "Get one free hint in any stage"},
    {"name": "Skip Power",           "category": "power", "price": 50,   "icon": "⏭️", "description": "Skip one difficult word"},
    {"name": "Double XP (1 day)",    "category": "power", "price": 100,  "icon": "⚡", "description": "Earn 2x XP for 24 hours"},
    {"name": "Sticker Pack",         "category": "real",  "price": 500,  "icon": "⭐", "description": "Real sticker pack from Dad!"},
    {"name": "Ice Cream Coupon",     "category": "real",  "price": 800,  "icon": "🍦", "description": "One ice cream from Dad!"},
    {"name": "Movie Night",          "category": "real",  "price": 1000, "icon": "🎬", "description": "Pick a movie for family night!"},
]


def _seed_rewards_if_empty(db: Session) -> None:
    """Insert seed rewards if the reward_items table is empty. @tag SHOP"""
    count = db.query(RewardItem).count()
    if count > 0:
        return
    from datetime import datetime
    now = datetime.now().isoformat()
    for item in SEED_REWARDS:
        db.add(RewardItem(
            name=item["name"],
            description=item.get("description", ""),
            category=item.get("category", "badge"),
            icon=item["icon"],
            price=item["price"],
            discount_pct=0,
            is_active=True,
            created_at=now,
        ))
    db.commit()
    logger.info("[shop] Seeded %d reward items", len(SEED_REWARDS))

DEFAULT_PIN = os.getenv("DEFAULT_PIN", "0000")


# ─── Schemas ──────────────────────────────────────────────────

class BuyIn(BaseModel):
    item_id: int


class UseRewardIn(BaseModel):
    pin: str


class SetPinIn(BaseModel):
    pin: str
    current_pin: str | None = None


class EquipIn(BaseModel):
    equip: bool = True


# ─── Helpers ──────────────────────────────────────────────────

def _final_price(item: RewardItem) -> int:
    """Return price after discount. @tag SHOP"""
    disc = max(0, min(100, item.discount_pct or 0))
    return max(0, round(item.price * (1 - disc / 100)))


def _get_pin(db: Session) -> str:
    """Retrieve current PIN from AppConfig; returns DEFAULT_PIN if not set. @tag PIN"""
    row = db.query(AppConfig).filter(AppConfig.key == "pin").first()
    return row.value if (row and row.value) else DEFAULT_PIN


def _item_dict(item: RewardItem) -> dict:
    """Serialize a RewardItem. @tag SHOP"""
    return {
        "id": item.id,
        "name": item.name,
        "description": getattr(item, "description", "") or "",
        "category": getattr(item, "category", "badge") or "badge",
        "icon": item.icon,
        "price": item.price,
        "discount_pct": item.discount_pct or 0,
        "final_price": _final_price(item),
        "is_active": item.is_active,
    }


def _purchase_dict(pr: PurchasedReward, item: RewardItem | None) -> dict:
    """Serialize a PurchasedReward with item info. @tag SHOP"""
    return {
        "id": pr.id,
        "item_id": pr.reward_item_id,
        "name": item.name if item else "Unknown",
        "description": getattr(item, "description", "") if item else "",
        "category": getattr(item, "category", "badge") if item else "badge",
        "icon": item.icon if item else "🎁",
        "xp_spent": pr.xp_spent,
        "is_used": pr.is_used,
        "is_equipped": getattr(pr, "is_equipped", False) or False,
        "purchased_at": pr.purchased_at,
        "used_at": pr.used_at,
    }


# ─── Endpoints ────────────────────────────────────────────────

@router.get("/api/shop/items")
def shop_items(
    category: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """
    Return all active reward shop items with final prices.
    Optional ?category=badge|theme|power|real filter.
    @tag SHOP
    """
    _seed_rewards_if_empty(db)
    q = db.query(RewardItem).filter(RewardItem.is_active == True)
    if category:
        q = q.filter(RewardItem.category == category)
    items = q.all()
    total_xp = xp_engine.get_total_xp(db)
    return {
        "items": [_item_dict(i) for i in items],
        "total_xp": total_xp,
    }


@router.post("/api/shop/buy")
def shop_buy(body: BuyIn, db: Session = Depends(get_db)):
    """
    Purchase a reward item. Deducts XP and creates a PurchasedReward.
    @tag SHOP XP
    """
    item = db.query(RewardItem).filter(
        RewardItem.id == body.item_id,
        RewardItem.is_active == True,
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    price = _final_price(item)
    # Atomic: balance check + XPLog spend + PurchasedReward insert all share
    # one BEGIN IMMEDIATE transaction. Double-click during network lag can't
    # double-spend, and a mid-op failure won't leave XP deducted without a
    # corresponding reward row.
    from sqlalchemy import text
    if db.in_transaction():
        db.rollback()
    db.execute(text("BEGIN IMMEDIATE"))
    try:
        current_xp = xp_engine.get_total_xp(db)
        if current_xp < price:
            db.rollback()
            raise HTTPException(status_code=400, detail="Not enough XP")

        now_iso = datetime.now().isoformat()
        today   = datetime.now().date().isoformat()
        # Import XPLog locally to avoid circular import at module top.
        from backend.models import XPLog
        db.add(XPLog(
            action="shop_purchase",
            xp_amount=-price,
            detail=item.name,
            earned_date=today,
            created_at=now_iso,
        ))
        pr = PurchasedReward(
            reward_item_id=item.id,
            xp_spent=price,
            is_used=False,
            purchased_at=now_iso,
            used_at=None,
        )
        db.add(pr)
        db.commit()
        db.refresh(pr)
    except HTTPException:
        raise
    except Exception:
        db.rollback()
        logger.exception("Purchase failed for item %s", item.id)
        raise HTTPException(status_code=500, detail="Purchase failed")

    return {
        "ok": True,
        "purchase_id": pr.id,
        "xp_spent": price,
        "remaining_xp": xp_engine.get_total_xp(db),
    }


@router.get("/api/shop/my-rewards")
def shop_my_rewards(db: Session = Depends(get_db)):
    """
    Return all purchased rewards (used and unused).
    @tag SHOP
    """
    purchases = (
        db.query(PurchasedReward)
        .order_by(PurchasedReward.purchased_at.desc())
        .all()
    )
    items_map = {i.id: i for i in db.query(RewardItem).all()}
    return {
        "rewards": [_purchase_dict(pr, items_map.get(pr.reward_item_id)) for pr in purchases],
        "total_xp": xp_engine.get_total_xp(db),
    }


@router.post("/api/shop/use-reward/{purchase_id}")
def shop_use_reward(purchase_id: int, body: UseRewardIn, db: Session = Depends(get_db)):
    """
    Mark a purchased reward as used after PIN verification.
    @tag SHOP PIN
    """
    # Rate-limit PIN attempts BEFORE looking up the purchase — attackers
    # shouldn't get timing info about which purchase IDs exist.
    pin_guard.assert_not_locked(db, "shop")

    pr = db.query(PurchasedReward).filter(PurchasedReward.id == purchase_id).first()
    if not pr:
        raise HTTPException(status_code=404, detail="Purchase not found")
    if pr.is_used:
        raise HTTPException(status_code=400, detail="Already used")

    stored_pin = _get_pin(db)
    if not pin_hash.verify_pin(body.pin or "", stored_pin):
        pin_guard.record_failure(db, "shop")
        raise HTTPException(status_code=403, detail="Wrong PIN")
    pin_guard.record_success(db, "shop")

    # Transparent migration: if the stored PIN is still legacy plaintext,
    # rewrite it as a pbkdf2 hash now that we know the caller has the right
    # value. Parent dashboard flow does the same thing in parent.py.
    row = db.query(AppConfig).filter(AppConfig.key == "pin").first()
    if row and pin_hash.needs_upgrade(row.value or ""):
        row.value = pin_hash.hash_pin(body.pin or "")
        row.updated_at = datetime.now().isoformat()

    pr.is_used = True
    pr.used_at = datetime.now().isoformat()
    db.commit()
    return {"ok": True}


@router.post("/api/shop/equip/{purchase_id}")
def shop_equip(purchase_id: int, body: EquipIn, db: Session = Depends(get_db)):
    """
    Equip or unequip a purchased reward (badges/themes).
    @tag SHOP
    """
    pr = db.query(PurchasedReward).filter(PurchasedReward.id == purchase_id).first()
    if not pr:
        raise HTTPException(status_code=404, detail="Purchase not found")
    if pr.is_used:
        raise HTTPException(status_code=400, detail="Already used/consumed")

    item = db.query(RewardItem).filter(RewardItem.id == pr.reward_item_id).first()
    cat = getattr(item, "category", "badge") if item else "badge"

    # For themes: unequip any other equipped theme first
    if body.equip and cat == "theme":
        theme_ids = [i.id for i in db.query(RewardItem).filter(RewardItem.category == "theme").all()]
        if theme_ids:
            db.query(PurchasedReward).filter(
                PurchasedReward.reward_item_id.in_(theme_ids),
                PurchasedReward.is_equipped == True,
            ).update({"is_equipped": False}, synchronize_session="fetch")

    pr.is_equipped = body.equip
    db.commit()
    return {"ok": True, "is_equipped": pr.is_equipped}


@router.get("/api/shop/pin-status")
def shop_pin_status(db: Session = Depends(get_db)):
    """
    Return whether a custom PIN has been set.
    @tag SHOP PIN
    """
    row = db.query(AppConfig).filter(AppConfig.key == "pin").first()
    # A row exists and is EITHER hashed (must be a real custom PIN —
    # DEFAULT_PIN is only ever stored plaintext) OR a plaintext row whose
    # value differs from DEFAULT_PIN. Both cases mean the initial setup ran.
    if not (row and row.value):
        return {"pin_set": False}
    if pin_hash.is_hashed(row.value):
        return {"pin_set": True}
    return {"pin_set": row.value != DEFAULT_PIN}


@router.post("/api/shop/set-pin")
def shop_set_pin(body: SetPinIn, db: Session = Depends(get_db)):
    """
    Set the 4-digit PIN (initial setup only).
    Once a PIN is set, it can only be changed via Parent Dashboard
    (POST /api/parent/config with X-Parent-Pin header).
    @tag SHOP PIN
    """
    if not body.pin.isdigit() or len(body.pin) != 4:
        raise HTTPException(status_code=400, detail="PIN must be exactly 4 digits")
    # Require knowledge of the current PIN (DEFAULT_PIN on fresh install) —
    # prevents an unauthenticated caller from hijacking the initial PIN setup.
    # `verify_pin` transparently handles hashed + legacy plaintext rows, and
    # falls back to DEFAULT_PIN when no row exists yet.
    existing = db.query(AppConfig).filter(AppConfig.key == "pin").first()
    current = existing.value if (existing and existing.value) else DEFAULT_PIN
    if not pin_hash.verify_pin(body.current_pin or "", current):
        raise HTTPException(status_code=403, detail="Current PIN required")
    # Refuse if a non-default PIN is already established — even a legacy
    # plaintext row counts, as long as it isn't DEFAULT_PIN.
    already_set = bool(existing and existing.value and (
        pin_hash.is_hashed(existing.value) or existing.value != DEFAULT_PIN
    ))
    if already_set:
        raise HTTPException(status_code=403, detail="PIN already set. Change it in Parent Dashboard.")
    now = datetime.now().isoformat()
    hashed = pin_hash.hash_pin(body.pin)
    if existing:
        existing.value = hashed
        existing.updated_at = now
    else:
        db.add(AppConfig(key="pin", value=hashed, updated_at=now))
    db.commit()
    return {"ok": True}
