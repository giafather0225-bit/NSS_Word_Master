"""
routers/island_shop.py — Island currency, shop, inventory, decor, sell (12 endpoints).
Section: Island
Dependencies: services.lumi_engine, models.island
API endpoints: /api/island/currency, /lumi/*, /shop, /inventory, /placed, /decorate/*, /inventory/sell
"""

import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.island import (
    IslandShopItem, IslandInventory, IslandPlacedItem, IslandLumiLog,
)
from backend.services import lumi_engine as le
from backend.routers._island_common import (
    BuyBody, EarnLumiBody, ExchangeBody, MoveBody, PlaceBody, RemoveBody, SellBody,
    cfg,
)

router = APIRouter(prefix="/api/island", tags=["island"])


# ─────────────────────────────────────────────────────────────────────────────
# 12.6 Currency
# ─────────────────────────────────────────────────────────────────────────────

# @tag ISLAND @tag XP
@router.get("/currency")
def currency_balance(db: Session = Depends(get_db)):
    return le.get_balance(db)


# @tag ISLAND @tag AWARD
@router.post("/lumi/earn")
def lumi_earn(body: EarnLumiBody, db: Session = Depends(get_db)):
    if body.amount <= 0:
        raise HTTPException(400, "amount must be positive.")
    result = le.earn_lumi(db, source=body.source, amount=body.amount,
                          character_progress_id=body.character_progress_id)
    db.commit()
    return result


# @tag ISLAND @tag SHOP
@router.post("/lumi/exchange")
def lumi_exchange(body: ExchangeBody, db: Session = Depends(get_db)):
    try:
        result = le.exchange_lumi(db, body.lumi_amount)
        db.commit()
        return result
    except le.InsufficientLumiError as e:
        raise HTTPException(400, str(e))
    except ValueError as e:
        raise HTTPException(400, str(e))


# @tag ISLAND
@router.get("/lumi/log")
def lumi_log(limit: int = Query(50, le=200), db: Session = Depends(get_db)):
    rows = (
        db.query(IslandLumiLog)
        .order_by(IslandLumiLog.created_at.desc())
        .limit(limit)
        .all()
    )
    return {"log": [
        {"id": r.id, "currency_type": r.currency_type, "action": r.action,
         "amount": r.amount, "source": r.source, "balance_after": r.balance_after,
         "legend_balance_after": r.legend_balance_after, "created_at": r.created_at}
        for r in rows
    ]}


# ─────────────────────────────────────────────────────────────────────────────
# 12.7 Shop & Inventory
# ─────────────────────────────────────────────────────────────────────────────

# @tag ISLAND @tag SHOP
@router.get("/shop")
def shop_catalog(category: Optional[str] = None, zone: Optional[str] = None,
                 db: Session = Depends(get_db)):
    q = db.query(IslandShopItem).filter(IslandShopItem.is_active == True)
    if category:
        q = q.filter(IslandShopItem.category == category)
    if zone:
        q = q.filter(IslandShopItem.zone.in_([zone, "all"]))
    items = q.order_by(IslandShopItem.category, IslandShopItem.price).all()
    currency = le.get_balance(db)
    inv_ids = {row.shop_item_id for row in db.query(IslandInventory.shop_item_id)
        .filter(IslandInventory.quantity > 0).all()}
    placed_ids = {row.shop_item_id for row in db.query(IslandPlacedItem.shop_item_id)
        .filter(IslandPlacedItem.is_placed == True).all()}
    owned_ids = sorted(inv_ids | placed_ids)
    return {
        "items": [
            {"id": i.id, "name": i.name, "category": i.category,
             "sub_category": i.sub_category, "zone": i.zone,
             "evolution_type": i.evolution_type, "price": i.price,
             "is_legend_currency": i.is_legend_currency,
             "image": i.image, "description": i.description}
            for i in items
        ],
        "currency": currency,
        "owned_ids": owned_ids,
    }


# @tag ISLAND @tag SHOP
@router.post("/shop/buy")
def shop_buy(body: BuyBody, db: Session = Depends(get_db)):
    item = db.get(IslandShopItem, body.shop_item_id)
    if item is None or not item.is_active:
        raise HTTPException(404, "Item not found.")

    if item.category == "decoration":
        if body.quantity != 1:
            raise HTTPException(400, "Decorations can only be bought one at a time.")
        existing_inv = db.query(IslandInventory).filter_by(
            shop_item_id=item.id, item_type="decoration",
            used_on_character_progress_id=None,
        ).first()
        if existing_inv and existing_inv.quantity > 0:
            raise HTTPException(400, f"You already own '{item.name}' (in inventory).")
        existing_placed = db.query(IslandPlacedItem).filter_by(
            shop_item_id=item.id, is_placed=True,
        ).first()
        if existing_placed:
            raise HTTPException(400, f"You already placed '{item.name}' in your island.")

    test_mode = cfg(db, "test_mode") == "true"
    total_cost = item.price * body.quantity
    if not test_mode:
        try:
            if item.is_legend_currency:
                le.spend_legend_lumi(db, total_cost, source="shop")
            else:
                le.spend_lumi(db, total_cost, source="shop")
        except le.InsufficientLumiError as e:
            raise HTTPException(400, str(e))

    inv = db.query(IslandInventory).filter_by(
        shop_item_id=item.id, item_type=item.category,
        used_on_character_progress_id=None,
    ).first()
    if inv:
        inv.quantity += body.quantity
    else:
        inv = IslandInventory(
            shop_item_id=item.id,
            item_type=item.category,
            quantity=body.quantity,
            purchased_at=datetime.now(timezone.utc),
        )
        db.add(inv)

    db.commit()
    return {"ok": True, "item": item.name, "quantity": body.quantity,
            "total_cost": total_cost, "currency": le.get_balance(db)}


# @tag ISLAND
@router.get("/inventory")
def inventory(category: Optional[str] = None, db: Session = Depends(get_db)):
    q = (
        db.query(IslandInventory, IslandShopItem)
        .join(IslandShopItem, IslandInventory.shop_item_id == IslandShopItem.id)
        .filter(IslandInventory.quantity > 0)
    )
    if category:
        q = q.filter(IslandInventory.item_type == category)
    rows = q.all()
    return {"items": [
        {"id": inv.id, "shop_item_id": inv.shop_item_id, "item_type": inv.item_type,
         "quantity": inv.quantity, "name": si.name, "category": si.category,
         "sub_category": si.sub_category, "zone": si.zone,
         "evolution_type": si.evolution_type, "image": si.image,
         "used_on_character_progress_id": inv.used_on_character_progress_id}
        for inv, si in rows
    ]}


# @tag ISLAND
@router.get("/placed")
def placed_items(zone: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(IslandPlacedItem, IslandShopItem).join(
        IslandShopItem, IslandPlacedItem.shop_item_id == IslandShopItem.id
    ).filter(IslandPlacedItem.is_placed == True)
    if zone:
        q = q.filter(IslandPlacedItem.zone == zone)
    rows = q.all()
    return {"items": [
        {"id": p.id, "shop_item_id": p.shop_item_id, "zone": p.zone,
         "pos_x": p.pos_x, "pos_y": p.pos_y,
         "name": si.name, "image": si.image, "sub_category": si.sub_category}
        for p, si in rows
    ]}


# @tag ISLAND
@router.post("/decorate/place")
def decorate_place(body: PlaceBody, db: Session = Depends(get_db)):
    inv = db.get(IslandInventory, body.inventory_id)
    if inv is None or inv.item_type != "decoration" or inv.quantity <= 0:
        raise HTTPException(400, "Decoration not available in inventory.")

    si = db.get(IslandShopItem, inv.shop_item_id)
    if si and si.zone not in (body.zone, "all"):
        raise HTTPException(400, f"This decoration cannot be placed in zone '{body.zone}'.")

    placed = db.query(IslandPlacedItem).filter_by(shop_item_id=inv.shop_item_id).first()
    if placed:
        placed.is_placed = True
        placed.zone = body.zone
        placed.pos_x = body.pos_x
        placed.pos_y = body.pos_y
        placed.placed_at = datetime.now(timezone.utc)
    else:
        placed = IslandPlacedItem(
            shop_item_id=inv.shop_item_id, zone=body.zone,
            pos_x=body.pos_x, pos_y=body.pos_y,
            placed_at=datetime.now(timezone.utc),
        )
        db.add(placed)

    inv.quantity -= 1
    db.commit()
    return {"ok": True, "zone": body.zone}


# @tag ISLAND
@router.post("/decorate/move")
def decorate_move(body: MoveBody, db: Session = Depends(get_db)):
    """Reposition a placed decoration without returning it to inventory."""
    placed = db.get(IslandPlacedItem, body.placed_item_id)
    if placed is None or not placed.is_placed:
        raise HTTPException(404, "Placed item not found.")
    placed.pos_x = max(0, min(100, body.pos_x))
    placed.pos_y = max(0, min(100, body.pos_y))
    db.commit()
    return {"ok": True, "pos_x": placed.pos_x, "pos_y": placed.pos_y}


# @tag ISLAND
@router.post("/decorate/remove")
def decorate_remove(body: RemoveBody, db: Session = Depends(get_db)):
    placed = db.get(IslandPlacedItem, body.placed_item_id)
    if placed is None or not placed.is_placed:
        raise HTTPException(404, "Placed item not found.")
    placed.is_placed = False

    inv = db.query(IslandInventory).filter_by(
        shop_item_id=placed.shop_item_id, item_type="decoration",
        used_on_character_progress_id=None,
    ).first()
    if inv:
        inv.quantity += 1
    else:
        db.add(IslandInventory(
            shop_item_id=placed.shop_item_id, item_type="decoration", quantity=1,
            purchased_at=datetime.now(timezone.utc),
        ))
    db.commit()
    return {"ok": True}


# @tag ISLAND
@router.post("/inventory/sell")
def inventory_sell(body: SellBody, db: Session = Depends(get_db)):
    """
    Sell a decoration from inventory for 50% Lumi refund.

    Rules:
    - Only category='decoration' items can be sold.
    - Cannot sell if the item is currently placed on the island.
    - Refund = floor(shop_item.price * 0.5), minimum 1 Lumi.
    - Decrements inventory quantity by 1; deletes row if quantity reaches 0.
    """
    inv = db.get(IslandInventory, body.inventory_id)
    if inv is None or inv.quantity <= 0:
        raise HTTPException(404, "Inventory item not found.")
    if inv.item_type != "decoration":
        raise HTTPException(400, "Only decoration items can be sold.")

    placed = db.query(IslandPlacedItem).filter_by(
        shop_item_id=inv.shop_item_id, is_placed=True,
    ).first()
    if placed:
        raise HTTPException(400, "Remove the decoration from your island before selling it.")

    si = db.get(IslandShopItem, inv.shop_item_id)
    if si is None:
        raise HTTPException(500, "Shop item data missing.")

    refund = max(1, int(si.price * 0.5))

    inv.quantity -= 1
    if inv.quantity <= 0:
        db.delete(inv)

    balance = le.earn_lumi(db, refund, source=f"sell_decor_{si.id}")

    db.commit()
    return {
        "ok": True,
        "item_name": si.name,
        "refund": refund,
        "lumi": balance["lumi"],
        "legend_lumi": balance["legend_lumi"],
    }
