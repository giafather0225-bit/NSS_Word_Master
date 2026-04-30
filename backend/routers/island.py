"""
routers/island.py — Island system REST API (34 endpoints).
Section: Island
Dependencies: services.lumi_engine, island_care_engine, island_production_engine, island_service
API endpoints: /api/island/*
"""

import json
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.island import (
    IslandCharacter, IslandCharacterProgress, IslandCareLog,
    IslandShopItem, IslandInventory, IslandPlacedItem,
    IslandLumiLog, IslandLegendProgress, IslandZoneStatus,
)
from backend.models.gamification import XPLog
from backend.models.system import AppConfig
from backend.services import lumi_engine as le
from backend.services import island_care_engine as care
from backend.services import island_production_engine as prod
from backend.services import island_service as svc
from backend.services.island_service import EvolutionError

router = APIRouter(prefix="/api/island", tags=["island"])

# ── Config key whitelist for public reads ─────────────────────────────────────
_ISLAND_CONFIG_KEYS = {
    "island_initialized", "island_on", "lumi_exchange_rate",
    "lumi_rule_english_stage", "lumi_rule_english_final",
    "lumi_rule_math_lesson", "lumi_rule_math_unit",
    "lumi_rule_diary", "lumi_rule_review", "lumi_rule_streak",
    "lumi_boost_total", "lumi_boost_english", "lumi_boost_math",
    "lumi_boost_diary", "lumi_boost_review",
}

_FOOD_XP = {"Small Food": 50, "Big Food": 150, "Special Food": 300}

# Subject detection from XPLog action for legend daily check.
_SUBJECT_ACTIONS: dict[str, set[str]] = {
    "english": {"word_correct", "stage_complete", "final_test_pass", "unit_test_pass",
                "daily_words_complete", "weekly_test_pass", "mywords_weekly_test_pass"},
    "math":    {"math_lesson_complete", "math_unit_test_pass", "math_kangaroo_complete",
                "math_kangaroo_80", "math_kangaroo_perfect"},
    "diary":   {"journal_complete"},
    "review":  {"review_complete"},
}


def _today() -> date:
    return datetime.now(timezone.utc).date()


def _today_start() -> datetime:
    return datetime.combine(_today(), datetime.min.time()).replace(tzinfo=timezone.utc)


def _cfg(db: Session, key: str, default: str = "") -> str:
    row = db.query(AppConfig).filter_by(key=key).first()
    return row.value if row else default


def _set_cfg(db: Session, key: str, value: str) -> None:
    row = db.query(AppConfig).filter_by(key=key).first()
    if row:
        row.value = value
    else:
        db.add(AppConfig(key=key, value=value))


def _prog_dict(prog: IslandCharacterProgress, char: IslandCharacter) -> dict:
    return {
        "id": prog.id,
        "character_id": prog.character_id,
        "name": char.name,
        "nickname": prog.nickname,
        "zone": char.zone,
        "subject": char.subject,
        "stage": prog.stage,
        "level": prog.level,
        "current_xp": prog.current_xp,
        "hunger": prog.hunger,
        "happiness": prog.happiness,
        "is_completed": prog.is_completed,
        "is_legend_type": prog.is_legend_type,
        "boost_active": prog.boost_active,
        "boost_subject": prog.boost_subject,
        "pos_x": prog.pos_x,
        "pos_y": prog.pos_y,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Pydantic schemas
# ─────────────────────────────────────────────────────────────────────────────

class ZoneUnlockBody(BaseModel):
    zone: str

class AdoptBody(BaseModel):
    character_id: int
    nickname: str = Field("", max_length=30)

class EvolveBody(BaseModel):
    character_progress_id: int
    stone_type: str

class FeedBody(BaseModel):
    character_progress_id: int
    inventory_id: int

class EarnLumiBody(BaseModel):
    source: str
    amount: int
    character_progress_id: Optional[int] = None

class ExchangeBody(BaseModel):
    lumi_amount: int

class BuyBody(BaseModel):
    shop_item_id: int
    quantity: int = 1

class PlaceBody(BaseModel):
    inventory_id: int
    zone: str
    pos_x: int = 0
    pos_y: int = 0

class RemoveBody(BaseModel):
    placed_item_id: int

class ConfigUpdateBody(BaseModel):
    key: str
    value: str


# ─────────────────────────────────────────────────────────────────────────────
# 12.1 Island Status & Onboarding
# ─────────────────────────────────────────────────────────────────────────────

# @tag ISLAND
@router.get("/status")
def island_status(db: Session = Depends(get_db)):
    """Full island state: zones, active characters, currency."""
    zones = db.query(IslandZoneStatus).all()
    active = (
        db.query(IslandCharacterProgress, IslandCharacter)
        .join(IslandCharacter, IslandCharacterProgress.character_id == IslandCharacter.id)
        .filter(IslandCharacterProgress.is_active == True,
                IslandCharacterProgress.is_completed == False)
        .all()
    )
    return {
        "island_on": _cfg(db, "island_on", "true") == "true",
        "initialized": _cfg(db, "island_initialized") == "true",
        "currency": le.get_balance(db),
        "zones": [{"zone": z.zone, "is_unlocked": z.is_unlocked} for z in zones],
        "active_characters": [_prog_dict(p, c) for p, c in active],
        "completed_count": db.query(IslandCharacterProgress)
            .filter(IslandCharacterProgress.is_completed == True).count(),
    }


# @tag ISLAND
@router.get("/onboarding/status")
def onboarding_status(db: Session = Depends(get_db)):
    return {"initialized": _cfg(db, "island_initialized") == "true"}


# @tag ISLAND
@router.post("/onboarding/complete")
def onboarding_complete(db: Session = Depends(get_db)):
    _set_cfg(db, "island_initialized", "true")
    db.commit()
    return {"ok": True}


# ─────────────────────────────────────────────────────────────────────────────
# 12.2 Zone Management
# ─────────────────────────────────────────────────────────────────────────────

# @tag ISLAND
@router.get("/zone/status")
def zone_status(db: Session = Depends(get_db)):
    rows = db.query(IslandZoneStatus).all()
    return {"zones": [
        {"zone": r.zone, "is_unlocked": r.is_unlocked, "unlocked_at": r.unlocked_at,
         "first_completed_at": r.first_completed_at}
        for r in rows
    ]}


# @tag ISLAND
@router.post("/zone/unlock")
def zone_unlock(body: ZoneUnlockBody, db: Session = Depends(get_db)):
    row = db.query(IslandZoneStatus).filter_by(zone=body.zone).first()
    if row is None:
        raise HTTPException(404, f"Zone '{body.zone}' not found.")
    if row.is_unlocked:
        return {"ok": True, "already_unlocked": True}
    row.is_unlocked = True
    row.unlocked_at = datetime.now(timezone.utc)
    db.commit()
    return {"ok": True, "zone": body.zone}


# ─────────────────────────────────────────────────────────────────────────────
# 12.3 Character Management
# ─────────────────────────────────────────────────────────────────────────────

# @tag ISLAND
@router.get("/characters")
def character_catalog(zone: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(IslandCharacter)
    if zone:
        q = q.filter(IslandCharacter.zone == zone)
    chars = q.order_by(IslandCharacter.zone, IslandCharacter.order_index).all()
    result = []
    for char in chars:
        progs = db.query(IslandCharacterProgress).filter_by(character_id=char.id).all()
        result.append({
            "id": char.id, "name": char.name, "zone": char.zone,
            "subject": char.subject, "order_index": char.order_index,
            "description": char.description, "is_legend": char.is_legend,
            "lumi_production": char.lumi_production, "is_available": char.is_available,
            "evo_first_xp": char.evo_first_xp, "evo_second_xp": char.evo_second_xp,
            "progress": [_prog_dict(p, char) for p in progs],
        })
    return {"characters": result}


# @tag ISLAND
@router.get("/character/active")
def character_active(zone: Optional[str] = None, db: Session = Depends(get_db)):
    q = (
        db.query(IslandCharacterProgress, IslandCharacter)
        .join(IslandCharacter, IslandCharacterProgress.character_id == IslandCharacter.id)
        .filter(IslandCharacterProgress.is_active == True,
                IslandCharacterProgress.is_completed == False)
    )
    if zone:
        q = q.filter(IslandCharacter.zone == zone)
    rows = q.all()
    return {"characters": [_prog_dict(p, c) for p, c in rows]}


# @tag ISLAND
@router.get("/character/completed")
def character_completed(db: Session = Depends(get_db)):
    rows = (
        db.query(IslandCharacterProgress, IslandCharacter)
        .join(IslandCharacter, IslandCharacterProgress.character_id == IslandCharacter.id)
        .filter(IslandCharacterProgress.is_completed == True)
        .all()
    )
    return {"characters": [_prog_dict(p, c) for p, c in rows]}


# @tag ISLAND
@router.get("/character/silhouette")
def character_silhouette(db: Session = Depends(get_db)):
    """Return all characters with adoptable/silhouette/locked status."""
    chars = db.query(IslandCharacter).order_by(
        IslandCharacter.zone, IslandCharacter.order_index).all()
    result = []
    for char in chars:
        has_prereq = True
        if char.unlock_requires_character_id:
            done = db.query(IslandCharacterProgress).filter(
                IslandCharacterProgress.character_id == char.unlock_requires_character_id,
                IslandCharacterProgress.is_completed == True,
            ).first()
            has_prereq = done is not None
        zone_unlocked = db.query(IslandZoneStatus).filter_by(
            zone=char.zone, is_unlocked=True).first() is not None
        result.append({
            "character_id": char.id, "name": char.name, "zone": char.zone,
            "order_index": char.order_index, "is_available": char.is_available,
            "zone_unlocked": zone_unlocked, "prereq_met": has_prereq,
            "adoptable": char.is_available and zone_unlocked and has_prereq,
        })
    return {"characters": result}


# @tag ISLAND
@router.post("/character/adopt")
def character_adopt(body: AdoptBody, db: Session = Depends(get_db)):
    char = db.get(IslandCharacter, body.character_id)
    if char is None:
        raise HTTPException(404, "Character not found.")
    if not char.is_available:
        raise HTTPException(400, "This character is not yet available.")
    # Verify prerequisite.
    if char.unlock_requires_character_id:
        done = db.query(IslandCharacterProgress).filter(
            IslandCharacterProgress.character_id == char.unlock_requires_character_id,
            IslandCharacterProgress.is_completed == True,
        ).first()
        if not done:
            raise HTTPException(400, "Complete the prerequisite character first.")
    prog = IslandCharacterProgress(
        character_id=char.id,
        nickname=body.nickname or char.name,
        is_legend_type=char.is_legend,
        adopted_at=datetime.now(timezone.utc),
    )
    db.add(prog)
    db.flush()
    db.commit()
    return _prog_dict(prog, char)


# @tag ISLAND
@router.post("/character/evolve")
def character_evolve(body: EvolveBody, db: Session = Depends(get_db)):
    try:
        result = svc.execute_evolution(db, body.character_progress_id, body.stone_type)
        db.commit()
        return result
    except EvolutionError as e:
        raise HTTPException(400, str(e))


# @tag ISLAND
@router.post("/evolve/validate")
def evolve_validate(body: EvolveBody, db: Session = Depends(get_db)):
    try:
        return svc.validate_evolution(db, body.character_progress_id, body.stone_type)
    except EvolutionError as e:
        return {"valid": False, "message": str(e)}


# @tag ISLAND
@router.get("/character/{progress_id}/history")
def character_history(progress_id: int, limit: int = Query(50, le=200),
                      db: Session = Depends(get_db)):
    logs = (
        db.query(IslandCareLog)
        .filter(IslandCareLog.character_progress_id == progress_id)
        .order_by(IslandCareLog.logged_at.desc())
        .limit(limit)
        .all()
    )
    return {"history": [
        {"id": l.id, "action": l.action, "hunger_change": l.hunger_change,
         "happiness_change": l.happiness_change, "source": l.source,
         "logged_at": l.logged_at}
        for l in logs
    ]}


# ─────────────────────────────────────────────────────────────────────────────
# 12.4 Care System
# ─────────────────────────────────────────────────────────────────────────────

# @tag ISLAND
@router.get("/care/{character_progress_id}")
def care_status(character_progress_id: int, db: Session = Depends(get_db)):
    prog = db.get(IslandCharacterProgress, character_progress_id)
    if prog is None:
        raise HTTPException(404, "Character progress not found.")
    char = db.get(IslandCharacter, prog.character_id)

    # XP threshold — first evo uses evo_first_xp, second uses evo_second_xp
    stage = prog.stage or "baby"
    is_mid = stage in ("mid_a", "mid_b")
    is_final = stage in ("final_a", "final_b")
    xp_to_next = (char.evo_second_xp if is_mid else char.evo_first_xp) if char else 100
    current_xp = prog.current_xp or 0

    # Determine which stone is needed and whether evolution is possible
    if is_final or prog.is_completed:
        stone_needed = "None"
        can_evolve = False
    elif prog.is_legend_type:
        stone_needed = "legend_first_a" if stage == "baby" else "legend_second"
        can_evolve = current_xp >= xp_to_next and prog.hunger >= 20 and prog.happiness >= 20
    else:
        stone_needed = ("first_a" if stage == "baby" else "second")
        can_evolve = current_xp >= xp_to_next and prog.hunger >= 20 and prog.happiness >= 20

    # Legend streak
    legend_prog = None
    if prog.is_legend_type:
        legend_prog = db.query(IslandLegendProgress).filter_by(
            character_id=prog.character_id
        ).first()

    return {
        "character_progress_id": character_progress_id,
        "hunger": prog.hunger, "happiness": prog.happiness,
        "xp_multiplier": care.get_xp_multiplier(db, character_progress_id),
        "is_legend_type": prog.is_legend_type,
        "is_completed": prog.is_completed,
        "name": char.name if char else "",
        "current_xp": current_xp,
        "xp_to_next_level": xp_to_next,
        "can_evolve": can_evolve,
        "evolution_stone": stone_needed,
        "progress": {
            "id": prog.id,
            "character_id": prog.character_id,
            "character_name": char.name if char else "",
            "nickname": prog.nickname,
            "stage": stage,
            "level": prog.level or 1,
            "current_xp": current_xp,
            "hunger": prog.hunger,
            "happiness": prog.happiness,
            "is_legend_type": prog.is_legend_type,
            "is_completed": prog.is_completed,
            "consecutive_days": legend_prog.consecutive_days if legend_prog else 0,
        },
    }


# @tag ISLAND
@router.post("/care/feed")
def care_feed(body: FeedBody, db: Session = Depends(get_db)):
    inv = db.get(IslandInventory, body.inventory_id)
    if inv is None or inv.item_type != "food" or inv.quantity <= 0:
        raise HTTPException(400, "Food item not available in inventory.")
    shop_item = db.get(IslandShopItem, inv.shop_item_id)
    if shop_item is None:
        raise HTTPException(400, "Shop item not found.")

    # Daily limit: 1 use per food type per character per day.
    used_today = db.query(IslandCareLog).filter(
        IslandCareLog.character_progress_id == body.character_progress_id,
        IslandCareLog.source == f"food_{shop_item.id}",
        IslandCareLog.logged_at >= _today_start(),
    ).first()
    if used_today:
        raise HTTPException(400, f"{shop_item.name} already used on this character today.")

    xp_gain = _FOOD_XP.get(shop_item.name, 50)
    prog = db.get(IslandCharacterProgress, body.character_progress_id)
    if prog is None:
        raise HTTPException(404, "Character progress not found.")
    prog.current_xp += xp_gain
    inv.quantity -= 1
    inv.used_on_character_progress_id = body.character_progress_id

    db.add(IslandCareLog(
        character_progress_id=body.character_progress_id,
        action="feed",
        hunger_change=0,
        happiness_change=0,
        source=f"food_{shop_item.id}",
        logged_at=datetime.now(timezone.utc),
    ))
    db.commit()
    return {"ok": True, "xp_gained": xp_gain, "current_xp": prog.current_xp,
            "item_name": shop_item.name}


# ─────────────────────────────────────────────────────────────────────────────
# 12.5 Daily Processing
# ─────────────────────────────────────────────────────────────────────────────

# @tag ISLAND
@router.post("/daily")
def daily_batch(db: Session = Depends(get_db)):
    """App-open batch: decay all active characters + run lumi production."""
    decay_result = care.run_daily_batch(db)
    prod_result = prod.run_daily_production(db)
    db.commit()
    return {"decay": decay_result, "production": prod_result, "ok": True}


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
    }


# @tag ISLAND @tag SHOP
@router.post("/shop/buy")
def shop_buy(body: BuyBody, db: Session = Depends(get_db)):
    item = db.get(IslandShopItem, body.shop_item_id)
    if item is None or not item.is_active:
        raise HTTPException(404, "Item not found.")
    total_cost = item.price * body.quantity
    try:
        if item.is_legend_currency:
            le.spend_legend_lumi(db, total_cost, source="shop")
        else:
            le.spend_lumi(db, total_cost, source="shop")
    except le.InsufficientLumiError as e:
        raise HTTPException(400, str(e))

    # Upsert inventory row.
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
    q = db.query(IslandInventory, IslandShopItem).join(
        IslandShopItem, IslandInventory.shop_item_id == IslandShopItem.id)
    if category:
        q = q.filter(IslandInventory.item_type == category)
    rows = q.all()
    return {"items": [
        {"id": inv.id, "shop_item_id": inv.shop_item_id, "item_type": inv.item_type,
         "quantity": inv.quantity, "name": si.name, "category": si.category,
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
         "pos_x": p.pos_x, "pos_y": p.pos_y, "name": si.name, "image": si.image}
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
@router.post("/decorate/remove")
def decorate_remove(body: RemoveBody, db: Session = Depends(get_db)):
    placed = db.get(IslandPlacedItem, body.placed_item_id)
    if placed is None or not placed.is_placed:
        raise HTTPException(404, "Placed item not found.")
    placed.is_placed = False

    # Return to inventory.
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


# ─────────────────────────────────────────────────────────────────────────────
# 12.8 Legend System
# ─────────────────────────────────────────────────────────────────────────────

# @tag ISLAND
@router.get("/legend/progress")
def legend_progress(db: Session = Depends(get_db)):
    rows = db.query(IslandLegendProgress, IslandCharacter).join(
        IslandCharacter, IslandLegendProgress.character_id == IslandCharacter.id
    ).all()
    return {"progress": [
        {"id": lp.id, "character_id": lp.character_id, "name": char.name,
         "consecutive_days": lp.consecutive_days, "total_days": lp.total_days,
         "last_completed_date": str(lp.last_completed_date) if lp.last_completed_date else None,
         "is_unlocked": lp.is_unlocked, "is_completed": lp.is_completed}
        for lp, char in rows
    ]}


# @tag ISLAND
@router.post("/legend/daily")
def legend_daily(db: Session = Depends(get_db)):
    """Check 4-subject completion for today and update legend streak."""
    today = _today()
    today_start = _today_start()
    today_actions = {
        r.action for r in
        db.query(XPLog).filter(XPLog.created_at >= today_start).all()
    }
    subjects_done = {
        subj: bool(today_actions & actions)
        for subj, actions in _SUBJECT_ACTIONS.items()
    }
    all_four = all(subjects_done.values())

    if not all_four:
        return {"all_four_done": False, "subjects": subjects_done}

    # Find active legend character progress rows.
    legend_progs = (
        db.query(IslandCharacterProgress)
        .filter(IslandCharacterProgress.is_legend_type == True,
                IslandCharacterProgress.is_active == True)
        .all()
    )

    updated = []
    for prog in legend_progs:
        # Apply happiness gain.
        care.apply_study_gain(db, prog.id, "legend_4subject")

        # Update IslandLegendProgress for this character.
        lp = db.query(IslandLegendProgress).filter_by(character_id=prog.character_id).first()
        if lp is None:
            lp = IslandLegendProgress(character_id=prog.character_id)
            db.add(lp)
            db.flush()

        if lp.last_completed_date == today:
            continue  # already counted today

        # Reset streak if missed yesterday.
        if lp.last_completed_date and (today - lp.last_completed_date).days > 1:
            lp.consecutive_days = 0

        lp.consecutive_days += 1
        lp.total_days += 1
        lp.last_completed_date = today
        updated.append(prog.character_id)

    db.commit()
    return {"all_four_done": True, "subjects": subjects_done, "updated_characters": updated}


# @tag ISLAND
@router.get("/legend/unlock/status")
def legend_unlock_status(db: Session = Depends(get_db)):
    """Legend zone unlocks when each of the 4 main zones has >= 1 evolved character."""
    main_zones = ["forest", "ocean", "savanna", "space"]
    zone_status = {}
    for zone in main_zones:
        count = (
            db.query(IslandCharacterProgress)
            .join(IslandCharacter, IslandCharacterProgress.character_id == IslandCharacter.id)
            .filter(IslandCharacter.zone == zone,
                    IslandCharacterProgress.stage.in_(["mid_a", "mid_b", "final_a", "final_b"]))
            .count()
        )
        zone_status[zone] = count > 0

    all_unlocked = all(zone_status.values())
    if all_unlocked:
        legend_zone = db.query(IslandZoneStatus).filter_by(zone="legend").first()
        if legend_zone and not legend_zone.is_unlocked:
            legend_zone.is_unlocked = True
            legend_zone.unlocked_at = datetime.now(timezone.utc)
            db.commit()

    return {"zones": zone_status, "legend_unlocked": all_unlocked}


# ─────────────────────────────────────────────────────────────────────────────
# 12.9 Boost & Notifications
# ─────────────────────────────────────────────────────────────────────────────

# @tag ISLAND @tag XP
@router.get("/boost/status")
def boost_status(db: Session = Depends(get_db)):
    keys = ["lumi_boost_total", "lumi_boost_english", "lumi_boost_math",
            "lumi_boost_diary", "lumi_boost_review"]
    return {k: float(_cfg(db, k, "0")) for k in keys}


# @tag ISLAND
@router.get("/notifications")
def notifications(db: Session = Depends(get_db)):
    """Derive notifications from current gauge state."""
    items = []
    active = (
        db.query(IslandCharacterProgress, IslandCharacter)
        .join(IslandCharacter, IslandCharacterProgress.character_id == IslandCharacter.id)
        .filter(IslandCharacterProgress.is_active == True,
                IslandCharacterProgress.is_completed == False,
                IslandCharacterProgress.is_legend_type == False)
        .all()
    )
    for prog, char in active:
        if prog.hunger < 20:
            items.append({"type": "hunger_critical", "character": char.name,
                          "character_progress_id": prog.id, "value": prog.hunger})
        elif prog.hunger < 40:
            items.append({"type": "hunger_low", "character": char.name,
                          "character_progress_id": prog.id, "value": prog.hunger})
        if prog.happiness < 20:
            items.append({"type": "happiness_critical", "character": char.name,
                          "character_progress_id": prog.id, "value": prog.happiness})
    return {"notifications": items, "count": len(items)}


# @tag ISLAND
@router.post("/notifications/read")
def notifications_read():
    """Mark notifications read (stateless — derived from gauge state)."""
    return {"ok": True}


# ─────────────────────────────────────────────────────────────────────────────
# 12.10 Config & Stats
# ─────────────────────────────────────────────────────────────────────────────

# @tag ISLAND
@router.get("/config")
def island_config(db: Session = Depends(get_db)):
    rows = db.query(AppConfig).filter(AppConfig.key.in_(_ISLAND_CONFIG_KEYS)).all()
    return {"config": {r.key: r.value for r in rows}}


# @tag ISLAND
@router.post("/config/update")
def config_update(body: ConfigUpdateBody, db: Session = Depends(get_db)):
    if body.key not in _ISLAND_CONFIG_KEYS:
        raise HTTPException(400, f"Config key '{body.key}' is not editable here.")
    _set_cfg(db, body.key, body.value)
    db.commit()
    return {"ok": True, "key": body.key, "value": body.value}


# @tag ISLAND
@router.get("/stats/summary")
def stats_summary(db: Session = Depends(get_db)):
    """Basic island stats for parent dashboard."""
    total_chars = db.query(IslandCharacterProgress).count()
    completed = db.query(IslandCharacterProgress).filter(
        IslandCharacterProgress.is_completed == True).count()
    currency = le.get_balance(db)
    today_prod = prod.get_production_summary(db)
    return {
        "total_characters_raised": total_chars,
        "completed_characters": completed,
        "currency": currency,
        "lumi_produced_today": today_prod["today"],
        "boost": {k: float(_cfg(db, k, "0")) for k in [
            "lumi_boost_english", "lumi_boost_math",
            "lumi_boost_diary", "lumi_boost_review",
        ]},
    }
