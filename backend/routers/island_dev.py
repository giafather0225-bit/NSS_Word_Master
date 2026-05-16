"""
routers/island_dev.py — Island dev/test tools (7 endpoints, dev_mode gated).
Section: Island
Dependencies: models.island, services.lumi_engine
API endpoints: /api/island/dev/*
"""

import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.island import (
    IslandCharacter, IslandCharacterProgress, IslandCareLog,
    IslandShopItem, IslandInventory, IslandZoneStatus,
)
from backend.models.system import AppConfig
from backend.services import lumi_engine as le
from backend.routers._island_common import island_today

router = APIRouter(prefix="/api/island", tags=["island"])


def _require_dev_mode(db: Session) -> None:
    """Block dev endpoints unless app_config dev_mode = 'true'."""
    row = db.query(AppConfig).filter_by(key="dev_mode").first()
    if not row or row.value != "true":
        raise HTTPException(status_code=403, detail="Dev mode is disabled.")


# ─────────────────────────────────────────────────────────────────────────────
# Dev Tools (dev_mode only)
# ─────────────────────────────────────────────────────────────────────────────

# @tag ISLAND
@router.post("/dev/seed")
def dev_seed(db: Session = Depends(get_db)):
    """Add 9999 Lumi + 5 of each evolution stone + max gauges on active chars."""
    _require_dev_mode(db)
    le.earn_lumi(db, source="dev_seed", amount=9999, earned_date=island_today())
    stones = db.query(IslandShopItem).filter_by(category="evolution", is_active=True).all()
    for stone in stones:
        inv = db.query(IslandInventory).filter_by(shop_item_id=stone.id).first()
        if inv:
            inv.quantity += 5
        else:
            db.add(IslandInventory(shop_item_id=stone.id, item_type="evolution", quantity=5))
    active = db.query(IslandCharacterProgress).filter_by(is_active=True, is_completed=False).all()
    for char in active:
        char.hunger = 100
        char.happiness = 100
    db.commit()
    return {"ok": True, "lumi_added": 9999, "stones_seeded": len(stones)}


# @tag ISLAND
@router.post("/dev/level-up")
def dev_level_up(db: Session = Depends(get_db)):
    """Push active characters to max level of their current stage (evo-ready)."""
    _require_dev_mode(db)
    active = db.query(IslandCharacterProgress).filter_by(is_active=True, is_completed=False).all()
    for char in active:
        if char.stage == "baby":
            char.level = 5
            char.current_xp = 750
        elif char.stage in ("mid_a", "mid_b"):
            char.level = 10
            char.current_xp = 1900
    db.commit()
    return {"ok": True, "chars_updated": len(active)}


# @tag ISLAND
@router.post("/dev/unlock-zones")
def dev_unlock_zones(db: Session = Depends(get_db)):
    """Unlock all 5 zones instantly."""
    _require_dev_mode(db)
    zones = db.query(IslandZoneStatus).all()
    for z in zones:
        z.is_unlocked = True
    db.commit()
    return {"ok": True, "zones_unlocked": len(zones)}


# @tag ISLAND
@router.post("/dev/level-up-char/{progress_id}")
def dev_level_up_char(progress_id: int, db: Session = Depends(get_db)):
    """Increment a single character's level by 1 (capped at stage max). Test mode only."""
    _require_dev_mode(db)
    prog = db.get(IslandCharacterProgress, progress_id)
    if not prog:
        raise HTTPException(404, "Character progress not found.")
    if prog.is_completed:
        raise HTTPException(400, "Character is already completed.")
    stage = prog.stage or "baby"
    max_level = 10 if stage in ("mid_a", "mid_b") else 5
    if (prog.level or 1) >= max_level:
        xp_needed = 1900 if stage in ("mid_a", "mid_b") else 750
        prog.current_xp = xp_needed
    else:
        prog.level = (prog.level or 1) + 1
        prog.hunger = min(100, (prog.hunger or 0) + 10)
        prog.happiness = min(100, (prog.happiness or 0) + 10)
    db.commit()
    char = db.get(IslandCharacter, prog.character_id)
    return {"ok": True, "progress_id": progress_id, "level": prog.level,
            "current_xp": prog.current_xp, "stage": prog.stage,
            "name": char.name if char else "?"}


# @tag ISLAND
@router.post("/dev/evolve-char/{progress_id}")
def dev_evolve_char(progress_id: int, db: Session = Depends(get_db)):
    """Force-evolve a character to next stage, ignoring stone requirement. Test mode only."""
    _require_dev_mode(db)
    prog = db.get(IslandCharacterProgress, progress_id)
    if not prog:
        raise HTTPException(404, "Character progress not found.")
    if prog.is_completed:
        raise HTTPException(400, "Character already at final stage.")
    char = db.get(IslandCharacter, prog.character_id)
    stage = prog.stage or "baby"
    if stage == "baby":
        prog.stage = "mid_a"
        prog.level = 6
        prog.current_xp = 0
    elif stage in ("mid_a", "mid_b"):
        prog.stage = "final_a" if stage == "mid_a" else "final_b"
        prog.level = 10
        prog.is_completed = True
        prog.completed_at = datetime.now(timezone.utc)
        prog.lumi_production = (char.lumi_production or 5) if char else 5
    else:
        raise HTTPException(400, f"Cannot evolve from stage '{stage}'.")
    prog.hunger = 100
    prog.happiness = 100
    db.commit()
    return {"ok": True, "progress_id": progress_id, "new_stage": prog.stage,
            "is_completed": prog.is_completed, "name": char.name if char else "?"}


# @tag ISLAND
@router.post("/dev/delete-char/{progress_id}")
def dev_delete_char(progress_id: int, db: Session = Depends(get_db)):
    """Hard-delete a character progress record so it can be re-adopted. Test mode only."""
    _require_dev_mode(db)
    prog = db.get(IslandCharacterProgress, progress_id)
    if not prog:
        raise HTTPException(404, "Character progress not found.")
    char_name = db.get(IslandCharacter, prog.character_id)
    name = char_name.name if char_name else "?"
    db.query(IslandCareLog).filter_by(character_progress_id=progress_id).delete()
    db.delete(prog)
    db.commit()
    return {"ok": True, "deleted_progress_id": progress_id, "name": name}


# @tag ISLAND
@router.post("/dev/reset-char/{progress_id}")
def dev_reset_char(progress_id: int, db: Session = Depends(get_db)):
    """Reset a character back to baby stage, level 1, full gauges. Test mode only."""
    _require_dev_mode(db)
    prog = db.get(IslandCharacterProgress, progress_id)
    if not prog:
        raise HTTPException(404, "Character progress not found.")
    prog.stage = "baby"
    prog.level = 1
    prog.current_xp = 0
    prog.hunger = 100
    prog.happiness = 100
    prog.is_completed = False
    prog.completed_at = None
    prog.lumi_production = 0
    db.commit()
    char = db.get(IslandCharacter, prog.character_id)
    return {"ok": True, "progress_id": progress_id, "name": char.name if char else "?"}
