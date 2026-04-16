"""
routers/reward_shop.py — Reward Shop API
Section: System / Shop
Dependencies: models.py (RewardItem, PurchasedReward, AppConfig),
              services/xp_engine.py
API: GET /api/shop/items, POST /api/shop/buy,
     GET /api/shop/my-rewards, POST /api/shop/use-reward/{id},
     GET /api/shop/pin-status, POST /api/shop/set-pin
"""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

try:
    from ..database import get_db
    from ..models import AppConfig, PurchasedReward, RewardItem
    from ..services import xp_engine
except ImportError:
    from database import get_db
    from models import AppConfig, PurchasedReward, RewardItem
    from services import xp_engine

router = APIRouter()
logger = logging.getLogger(__name__)

DEFAULT_PIN = "0000"


# ─── Schemas ──────────────────────────────────────────────────

class BuyIn(BaseModel):
    item_id: int


class UseRewardIn(BaseModel):
    pin: str


class SetPinIn(BaseModel):
    pin: str


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
        "icon": item.icon if item else "🎁",
        "xp_spent": pr.xp_spent,
        "is_used": pr.is_used,
        "purchased_at": pr.purchased_at,
        "used_at": pr.used_at,
    }


# ─── Endpoints ────────────────────────────────────────────────

@router.get("/api/shop/items")
def shop_items(db: Session = Depends(get_db)):
    """
    Return all active reward shop items with final prices.
    @tag SHOP
    """
    items = db.query(RewardItem).filter(RewardItem.is_active == True).all()
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
    ok = xp_engine.spend_xp(db, price, detail=item.name)
    if not ok:
        raise HTTPException(status_code=400, detail="Not enough XP")

    pr = PurchasedReward(
        reward_item_id=item.id,
        xp_spent=price,
        is_used=False,
        purchased_at=datetime.now().isoformat(),
        used_at=None,
    )
    db.add(pr)
    db.commit()
    db.refresh(pr)

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
    pr = db.query(PurchasedReward).filter(PurchasedReward.id == purchase_id).first()
    if not pr:
        raise HTTPException(status_code=404, detail="Purchase not found")
    if pr.is_used:
        raise HTTPException(status_code=400, detail="Already used")

    correct_pin = _get_pin(db)
    if body.pin != correct_pin:
        raise HTTPException(status_code=403, detail="Wrong PIN")

    pr.is_used = True
    pr.used_at = datetime.now().isoformat()
    db.commit()
    return {"ok": True}


@router.get("/api/shop/pin-status")
def shop_pin_status(db: Session = Depends(get_db)):
    """
    Return whether a custom PIN has been set.
    @tag SHOP PIN
    """
    row = db.query(AppConfig).filter(AppConfig.key == "pin").first()
    is_set = bool(row and row.value and row.value != DEFAULT_PIN)
    return {"pin_set": is_set}


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
    # Block if a non-default PIN already exists — prevent child from resetting it
    existing = db.query(AppConfig).filter(AppConfig.key == "pin").first()
    if existing and existing.value and existing.value != DEFAULT_PIN:
        raise HTTPException(status_code=403, detail="PIN already set. Change it in Parent Dashboard.")
    now = datetime.now().isoformat()
    if existing:
        existing.value = body.pin
        existing.updated_at = now
    else:
        db.add(AppConfig(key="pin", value=body.pin, updated_at=now))
    db.commit()
    return {"ok": True}
