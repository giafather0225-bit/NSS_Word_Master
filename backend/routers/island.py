"""
routers/island.py — Island system REST API (34 endpoints).
Section: Island
Dependencies: services.lumi_engine, island_care_engine, island_production_engine, island_service
API endpoints: /api/island/*
"""

import json
import logging
from datetime import date, datetime, timedelta, timezone
from typing import Optional

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.island import (
    IslandCharacter, IslandCharacterProgress, IslandCareLog,
    IslandShopItem, IslandInventory, IslandPlacedItem,
    IslandLumiLog, IslandLegendProgress, IslandZoneStatus,
)
from backend.models.gamification import XPLog
from backend.models.goals import WeeklyGoal
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

# Zone sequential unlock chain (ISLAND_SPEC §Zone).
# When a character in zone[i] reaches is_completed, zone[i+1] auto-unlocks.
_ZONE_UNLOCK_CHAIN = ["forest", "ocean", "savanna", "space"]

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


def _prog_dict(
    prog: IslandCharacterProgress,
    char: IslandCharacter,
    consecutive_days: int = 0,
) -> dict:
    stage = prog.stage or "baby"
    is_mid   = stage in ("mid_a", "mid_b")
    is_final = stage in ("final_a", "final_b")
    xp_needed = (char.evo_second_xp if is_mid else char.evo_first_xp) if char else 100
    min_level = 10 if is_mid else 5
    ready_to_evolve = (
        not prog.is_completed
        and not is_final
        and (prog.current_xp or 0) >= xp_needed
        and (prog.level or 1) >= min_level
        and (prog.hunger or 0) >= 20
        and (prog.happiness or 0) >= 20
    )
    return {
        "id": prog.id,
        "character_id": prog.character_id,
        "name": char.name,
        "nickname": prog.nickname,
        "zone": char.zone,
        "subject": char.subject,
        "stage": stage,
        "level": prog.level,
        "current_xp": prog.current_xp,
        "hunger": prog.hunger,
        "happiness": prog.happiness,
        "is_completed": prog.is_completed,
        "is_legend_type": prog.is_legend_type,
        "boost_active": prog.boost_active,
        "boost_subject": prog.boost_subject,
        "ready_to_evolve": ready_to_evolve,
        "pos_x": prog.pos_x,
        "pos_y": prog.pos_y,
        "images": char.images or "{}",
        # For legend characters: days in current evolution streak.
        # Populated by callers that batch-load IslandLegendProgress; 0 for non-legend.
        "consecutive_days": consecutive_days,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Pydantic schemas
# ─────────────────────────────────────────────────────────────────────────────

class ZoneUnlockBody(BaseModel):
    zone: str = Field(max_length=50)

class AdoptBody(BaseModel):
    character_id: int
    nickname: str = Field("", max_length=30)

class EvolveBody(BaseModel):
    character_progress_id: int
    stone_type: str = Field("", max_length=50)

class EvolveBranchBody(BaseModel):
    character_progress_id: int
    branch: str = Field("", max_length=2)  # 'a' or 'b'; optional for /evolve/validate

class FeedBody(BaseModel):
    character_progress_id: int
    inventory_id: int

class EarnLumiBody(BaseModel):
    source: str = Field(max_length=100)
    amount: int
    character_progress_id: Optional[int] = None

class ExchangeBody(BaseModel):
    lumi_amount: int

class BuyBody(BaseModel):
    shop_item_id: int
    quantity: int = 1

class PlaceBody(BaseModel):
    inventory_id: int
    zone: str = Field(max_length=50)
    pos_x: int = 0
    pos_y: int = 0

class RemoveBody(BaseModel):
    placed_item_id: int

class MoveBody(BaseModel):
    placed_item_id: int
    pos_x: int = 0
    pos_y: int = 0

class SellBody(BaseModel):
    inventory_id: int

class ConfigUpdateBody(BaseModel):
    key: str = Field(max_length=100)
    value: str = Field(max_length=200)


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
    completed = (
        db.query(IslandCharacterProgress, IslandCharacter)
        .join(IslandCharacter, IslandCharacterProgress.character_id == IslandCharacter.id)
        .filter(IslandCharacterProgress.is_completed == True)
        .all()
    )
    return {
        "island_on": _cfg(db, "island_on", "true") == "true",
        "initialized": _cfg(db, "island_initialized") == "true",
        "currency": le.get_balance(db),
        "zones": [{"zone": z.zone, "is_unlocked": z.is_unlocked} for z in zones],
        "active_characters": [_prog_dict(p, c) for p, c in active],
        "completed_characters": [_prog_dict(p, c) for p, c in completed],
        "completed_count": len(completed),
    }


# @tag ISLAND
@router.get("/onboarding/status")
def onboarding_status(db: Session = Depends(get_db)):
    return {"initialized": _cfg(db, "island_initialized") == "true"}


# @tag ISLAND
@router.post("/onboarding/complete")
def onboarding_complete(db: Session = Depends(get_db)):
    """Mark island as initialized and unlock all 4 main zones.

    Zone 1-4 sequential opening is a UX-only onboarding effect; all main zones
    must be playable immediately after onboarding completes.
    """
    _set_cfg(db, "island_initialized", "true")
    now = datetime.now(timezone.utc)
    for zone in _ZONE_UNLOCK_CHAIN:   # ["forest","ocean","savanna","space"]
        row = db.query(IslandZoneStatus).filter_by(zone=zone).first()
        if row and not row.is_unlocked:
            row.is_unlocked = True
            row.unlocked_at = now
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

    # Load all progress rows in one query, then group by character_id (avoids N+1).
    char_ids = [c.id for c in chars]
    all_progs = (
        db.query(IslandCharacterProgress)
        .filter(IslandCharacterProgress.character_id.in_(char_ids))
        .all()
    ) if char_ids else []
    progs_by_char: dict[int, list] = {}
    for p in all_progs:
        progs_by_char.setdefault(p.character_id, []).append(p)

    char_map = {c.id: c for c in chars}
    result = []
    for char in chars:
        progs = progs_by_char.get(char.id, [])
        result.append({
            "id": char.id, "name": char.name, "zone": char.zone,
            "subject": char.subject, "order_index": char.order_index,
            "description": char.description, "is_legend": char.is_legend,
            "lumi_production": char.lumi_production, "is_available": char.is_available,
            "evo_first_xp": char.evo_first_xp, "evo_second_xp": char.evo_second_xp,
            "progress": [_prog_dict(p, char_map[p.character_id]) for p in progs],
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

    # Batch-load legend progress for any legend-type characters (avoids N+1).
    prog_ids = [p.id for p, _ in rows if p.is_legend_type]
    legend_days: dict[int, int] = {}
    if prog_ids:
        legend_rows = (
            db.query(IslandLegendProgress)
            .filter(IslandLegendProgress.character_progress_id.in_(prog_ids))
            .all()
        )
        legend_days = {lr.character_progress_id: lr.consecutive_days for lr in legend_rows}

    return {
        "characters": [
            _prog_dict(p, c, consecutive_days=legend_days.get(p.id, 0))
            for p, c in rows
        ]
    }


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
    """Return all characters with adoptable/silhouette/locked status.

    Optimised: loads zone_status and completed-character sets in two bulk queries
    instead of one query per character (avoids N+1 on a 25-row catalog).
    """
    chars = db.query(IslandCharacter).order_by(
        IslandCharacter.zone, IslandCharacter.order_index).all()

    # Bulk-load zone unlock status → {zone: bool}
    zone_unlocked_map: dict[str, bool] = {
        row.zone: bool(row.is_unlocked)
        for row in db.query(IslandZoneStatus).all()
    }

    # Bulk-load all completed character_ids → set (used for prereq check)
    completed_char_ids: set[int] = {
        row.character_id
        for row in db.query(IslandCharacterProgress.character_id)
        .filter(IslandCharacterProgress.is_completed == True)
        .all()
    }

    # Bulk-load character_ids that have an active (non-completed) progress → block re-adoption
    active_char_ids: set[int] = {
        row.character_id
        for row in db.query(IslandCharacterProgress.character_id)
        .filter(IslandCharacterProgress.is_completed == False)
        .all()
    }

    result = []
    for char in chars:
        has_prereq = (
            char.unlock_requires_character_id in completed_char_ids
            if char.unlock_requires_character_id
            else True
        )
        zone_unlocked = zone_unlocked_map.get(char.zone, False)
        not_active = char.id not in active_char_ids
        result.append({
            "character_id": char.id, "name": char.name, "zone": char.zone,
            "order_index": char.order_index, "is_available": char.is_available,
            "zone_unlocked": zone_unlocked, "prereq_met": has_prereq,
            "adoptable": char.is_available and zone_unlocked and has_prereq and not_active,
            "already_active": not not_active,
            "images": char.images or "{}",
            "lumi_production": char.lumi_production or 0,
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
    # Prevent duplicate active adoption (block only if a non-completed record exists).
    already_active = db.query(IslandCharacterProgress).filter(
        IslandCharacterProgress.character_id == char.id,
        IslandCharacterProgress.is_completed == False,
    ).first()
    if already_active:
        raise HTTPException(400, "This character is already being raised.")
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
        is_active=True,
        adopted_at=datetime.now(timezone.utc),
    )
    db.add(prog)
    db.flush()
    db.commit()
    return _prog_dict(prog, char)


# @tag ISLAND
@router.post("/character/evolve")
def character_evolve(body: EvolveBranchBody, db: Session = Depends(get_db)):
    """Evolve a character by choosing branch 'a' or 'b'.
    Derives stone_type from the character's current stage and branch selection.
    """
    prog = db.get(IslandCharacterProgress, body.character_progress_id)
    if prog is None:
        raise HTTPException(404, "Character progress not found.")
    stage = prog.stage or "baby"
    branch = (body.branch or "a").lower()
    if prog.is_legend_type:
        stone = "legend_first_a" if stage == "baby" and branch == "a" else \
                "legend_first_b" if stage == "baby" and branch == "b" else \
                "legend_second"
    else:
        stone = "first_a" if stage == "baby" and branch == "a" else \
                "first_b" if stage == "baby" and branch == "b" else \
                "second"
    try:
        result = svc.execute_evolution(db, body.character_progress_id, stone)

        # ── Legend zone unlock: all 4 main zones need ≥1 first-evolution char ──
        # Zones 1-4 are unlocked sequentially during onboarding (character adoption).
        # Legend unlocks automatically the moment every main zone has a character
        # that has completed its first evolution (stage = mid_a or mid_b or beyond).
        new_stage = result.get("new_stage", "")
        _FIRST_EVO_STAGES = {"mid_a", "mid_b", "final_a", "final_b"}
        if new_stage in _FIRST_EVO_STAGES and not prog.is_legend_type:
            legend_row = db.query(IslandZoneStatus).filter_by(zone="legend").first()
            if legend_row and not legend_row.is_unlocked:
                all_first_evo = all(
                    db.query(IslandCharacterProgress)
                      .join(IslandCharacter, IslandCharacter.id == IslandCharacterProgress.character_id)
                      .filter(
                          IslandCharacter.zone == z,
                          IslandCharacterProgress.stage.in_(list(_FIRST_EVO_STAGES)),
                      ).count() >= 1
                    for z in _ZONE_UNLOCK_CHAIN  # ["forest","ocean","savanna","space"]
                )
                if all_first_evo:
                    legend_row.is_unlocked = True
                    legend_row.unlocked_at = datetime.now(timezone.utc)
                    result["zone_unlocked"] = "legend"
                    logger.info("Legend zone unlocked — all 4 main zones have first-evolution characters")

        # ── Sequential zone unlock: completing zone[i] → unlock zone[i+1] ──
        # A character is "completed" when it reaches final_a or final_b (is_completed=True).
        # This triggers the next zone in _ZONE_UNLOCK_CHAIN to open for new adoption.
        if result.get("is_completed") and not prog.is_legend_type:
            char = db.get(IslandCharacter, prog.character_id)
            if char and char.zone in _ZONE_UNLOCK_CHAIN:
                idx = _ZONE_UNLOCK_CHAIN.index(char.zone)
                if idx + 1 < len(_ZONE_UNLOCK_CHAIN):
                    next_zone = _ZONE_UNLOCK_CHAIN[idx + 1]
                    next_row = db.query(IslandZoneStatus).filter_by(zone=next_zone).first()
                    if next_row and not next_row.is_unlocked:
                        next_row.is_unlocked = True
                        next_row.unlocked_at = datetime.now(timezone.utc)
                        # Only overwrite if legend hasn't already claimed this key.
                        if "zone_unlocked" not in result:
                            result["zone_unlocked"] = next_zone
                        logger.info(
                            "Zone '%s' unlocked — character '%s' completed in zone '%s'",
                            next_zone, char.name, char.zone,
                        )

        db.commit()
        return result
    except EvolutionError as e:
        raise HTTPException(400, str(e))


# @tag ISLAND
@router.post("/evolve/validate")
def evolve_validate(body: EvolveBranchBody, db: Session = Depends(get_db)):
    """Return both evolution branches for a character so the UI can present a choice."""
    prog = db.get(IslandCharacterProgress, body.character_progress_id)
    if prog is None:
        return {"valid": False, "message": "Character progress not found."}
    stage = prog.stage or "baby"
    is_mid = stage in ("mid_a", "mid_b")
    is_final = stage in ("final_a", "final_b")

    if is_final or prog.is_completed:
        return {"valid": False, "message": "Character is already fully evolved."}

    char = db.get(IslandCharacter, prog.character_id)
    xp_to_next = (char.evo_second_xp if is_mid else char.evo_first_xp) if char else 100
    current_xp = prog.current_xp or 0

    if current_xp < xp_to_next:
        return {"valid": False, "message": f"Not enough XP. Need {xp_to_next}, have {current_xp}."}
    if not prog.is_legend_type and (prog.hunger < 20 or prog.happiness < 20):
        return {"valid": False, "message": "Hunger and happiness must both be above 20 to evolve."}

    if prog.is_legend_type:
        stone_a = "legend_first_a" if not is_mid else "legend_second"
        stone_b = "legend_first_b" if not is_mid else "legend_second"
    else:
        stone_a = "first_a" if not is_mid else "second"
        stone_b = "first_b" if not is_mid else "second"

    target_a = "mid_a" if not is_mid else "final_a"
    target_b = "mid_b" if not is_mid else "final_b"

    return {
        "valid": True,
        "stage": stage,
        "branch_a": {
            "stone": stone_a,
            "target_stage": target_a,
            "description": f"Evolve into {target_a} form.",
        },
        "branch_b": {
            "stone": stone_b,
            "target_stage": target_b,
            "description": f"Evolve into {target_b} form.",
        },
    }


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
        min_level = 10 if is_mid else 5
        can_evolve = current_xp >= xp_to_next and (prog.level or 1) >= min_level and prog.hunger >= 20 and prog.happiness >= 20
    else:
        stone_needed = ("first_a" if stage == "baby" else "second")
        min_level = 10 if is_mid else 5
        can_evolve = current_xp >= xp_to_next and (prog.level or 1) >= min_level and prog.hunger >= 20 and prog.happiness >= 20

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
            "images": char.images or "{}",
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
    # Source is logged as "food_{id}_xp{gain}" so match with LIKE prefix.
    used_today = db.query(IslandCareLog).filter(
        IslandCareLog.character_progress_id == body.character_progress_id,
        IslandCareLog.source.like(f"food_{shop_item.id}_%"),
        IslandCareLog.logged_at >= _today_start(),
    ).first()
    if used_today:
        raise HTTPException(400, f"{shop_item.name} already used on this character today.")

    xp_gain = _FOOD_XP.get(shop_item.name)
    if xp_gain is None:
        logger.warning("Unknown food item name %r (id=%s) — defaulting to 50 XP. "
                       "Update _FOOD_XP if the shop catalog changed.", shop_item.name, shop_item.id)
        xp_gain = 50
    prog = db.get(IslandCharacterProgress, body.character_progress_id)
    if prog is None:
        raise HTTPException(404, "Character progress not found.")

    level_before = care._calc_level(prog.current_xp or 0)
    prog.current_xp = (prog.current_xp or 0) + xp_gain
    level_after  = care._calc_level(prog.current_xp)
    if level_after != prog.level:
        prog.level = level_after

    # Consume inventory: decrement quantity and remove row when exhausted.
    inv.quantity -= 1
    inv.used_on_character_progress_id = body.character_progress_id
    if inv.quantity <= 0:
        db.delete(inv)

    # Food gives XP (not hunger/happiness). Encode xp_gained in source so
    # the care history view can display it meaningfully.
    db.add(IslandCareLog(
        character_progress_id=body.character_progress_id,
        action="feed",
        hunger_change=0,
        happiness_change=0,
        source=f"food_{shop_item.id}_xp{xp_gain}",
        logged_at=datetime.now(timezone.utc),
    ))
    db.commit()
    level_up = level_after > level_before
    return {"ok": True, "xp_gained": xp_gain, "current_xp": prog.current_xp,
            "item_name": shop_item.name,
            "level_up": level_up, "new_level": level_after}


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
    # Owned = currently in inventory (qty>0) OR currently placed in a zone.
    # For decorations this is unique-per-island; the buy endpoint rejects re-buys.
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

    # Decorations are unique-per-island: each can only be owned once.
    # Reject if user already has it in inventory OR already placed in a zone.
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

    # Block sell if this decoration is currently placed.
    placed = db.query(IslandPlacedItem).filter_by(
        shop_item_id=inv.shop_item_id, is_placed=True,
    ).first()
    if placed:
        raise HTTPException(400, "Remove the decoration from your island before selling it.")

    si = db.get(IslandShopItem, inv.shop_item_id)
    if si is None:
        raise HTTPException(500, "Shop item data missing.")

    refund = max(1, int(si.price * 0.5))

    # Decrement inventory.
    inv.quantity -= 1
    if inv.quantity <= 0:
        db.delete(inv)

    # Credit Lumi.
    balance = le.earn_lumi(db, refund, source=f"sell_decor_{si.id}")

    db.commit()
    return {
        "ok": True,
        "item_name": si.name,
        "refund": refund,
        "lumi": balance["lumi"],
        "legend_lumi": balance["legend_lumi"],
    }


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

        # Reset streak if missed yesterday; apply happiness -10 on break.
        if lp.last_completed_date and (today - lp.last_completed_date).days > 1:
            if lp.consecutive_days > 0:
                # Happiness penalty — only when streak was actually active.
                prog.happiness = max(0, (prog.happiness or 0) - 10)
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
    # NOTE: Do NOT auto-unlock here — this is a read-only GET endpoint.
    # Legend zone unlocking is handled by /character/evolve (see lines ~420-440).
    # Auto-unlock in a GET causes side-effects and violates REST semantics.
    legend_zone = db.query(IslandZoneStatus).filter_by(zone="legend").first()
    legend_in_db = bool(legend_zone and legend_zone.is_unlocked)

    return {"zones": zone_status, "legend_unlocked": legend_in_db}


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
    """Derive notifications: hungry/unhappy chars, evolvable chars, today's lumi production.

    Also exposes `active_char` — the first non-completed active character's current state —
    so that the post-study island-result card (island-result.js) can display gauge values
    and character name without a second API call.

    Returns:
        {
          hungry:      [{nickname, name, hunger, happiness}, ...],
          evolvable:   [{nickname, name}, ...],
          lumi_earned: int,
          active_char: {name, hunger, happiness} | null
        }
    """
    hungry: list[dict] = []
    evolvable: list[dict] = []
    active_char: Optional[dict] = None

    active = (
        db.query(IslandCharacterProgress, IslandCharacter)
        .join(IslandCharacter, IslandCharacterProgress.character_id == IslandCharacter.id)
        .filter(
            IslandCharacterProgress.is_active == True,
            IslandCharacterProgress.is_completed == False,
        )
        .all()
    )
    for prog, char in active:
        # Capture first non-legend raising character for island-result card
        if active_char is None and not prog.is_legend_type:
            active_char = {
                "name":      prog.nickname or char.name,
                "hunger":    prog.hunger,
                "happiness": prog.happiness,
            }

        # Hunger / happiness alerts
        if (not prog.is_legend_type) and (prog.hunger < 40 or prog.happiness < 40):
            hungry.append({
                "nickname":  prog.nickname or char.name,
                "name":      char.name,
                "hunger":    prog.hunger,
                "happiness": prog.happiness,
            })

        # Evolvable check (same logic as care_status)
        if not prog.is_legend_type:
            stage = prog.stage or "baby"
            is_final = stage in ("final_a", "final_b")
            xp_needed = (char.evo_second_xp if stage in ("mid_a", "mid_b") else char.evo_first_xp) if char else 100
            if not is_final and not prog.is_completed:
                if (prog.current_xp or 0) >= xp_needed and prog.hunger >= 20 and prog.happiness >= 20:
                    evolvable.append({"nickname": prog.nickname or char.name, "name": char.name})

    # lumi_earned = lumi gained from study activity today (not passive production).
    # Sum all today's lumi_log entries whose source is not production/dev/exchange.
    _PASSIVE_PREFIXES = ("production", "dev_", "exchange", "daily_attendance")
    today_logs = (
        db.query(IslandLumiLog)
        .filter(IslandLumiLog.earned_date == _today())
        .all()
    )
    lumi_earned = sum(
        lg.amount for lg in today_logs
        if not any(lg.source.startswith(p) for p in _PASSIVE_PREFIXES)
    )
    return {
        "hungry":      hungry,
        "evolvable":   evolvable,
        "lumi_earned": lumi_earned,
        "active_char": active_char,
    }


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


# ─────────────────────────────────────────────────────────────────────────────
# 12.12 Daily Screen
# ─────────────────────────────────────────────────────────────────────────────

# @tag ISLAND
@router.get("/daily")
def daily_screen(db: Session = Depends(get_db)):
    """Return all data needed for the Daily attendance / missions / goals screen."""
    from backend.services import streak_engine
    from sqlalchemy import func as sqlfunc

    today      = _today()
    week_start = today - timedelta(days=today.weekday())  # Monday

    streak = streak_engine.get_current_streak(db)

    attendance_week = []
    for offset in range(7):
        day = week_start + timedelta(days=offset)
        attended = db.query(XPLog).filter(
            XPLog.earned_date == day.isoformat()
        ).first() is not None
        claimed = db.query(IslandLumiLog).filter(
            IslandLumiLog.source == "daily_attendance",
            IslandLumiLog.earned_date == day,
        ).first() is not None
        attendance_week.append({
            "date":     day.isoformat(),
            "attended": attended,
            "claimed":  claimed,
            "today":    day == today,
        })

    can_claim_today = (
        db.query(XPLog).filter(XPLog.earned_date == today.isoformat()).first() is not None
        and not db.query(IslandLumiLog).filter(
            IslandLumiLog.source == "daily_attendance",
            IslandLumiLog.earned_date == today,
        ).first()
    )
    today_claimed = db.query(IslandLumiLog).filter(
        IslandLumiLog.source == "daily_attendance",
        IslandLumiLog.earned_date == today,
    ).first() is not None

    ATTENDANCE_REWARD = 30

    today_actions = {
        r.action for r in db.query(XPLog).filter(
            XPLog.earned_date == today.isoformat()
        ).all()
    }

    missions = [
        {
            "id":          "english",
            "title":       "Study English",
            "description": "Complete any English activity today",
            "reward_lumi": 20,
            "progress":    1 if today_actions & _SUBJECT_ACTIONS["english"] else 0,
            "total":       1,
            "completed":   bool(today_actions & _SUBJECT_ACTIONS["english"]),
            "locked":      False,
        },
        {
            "id":          "math",
            "title":       "Study Math",
            "description": "Complete any Math activity today",
            "reward_lumi": 20,
            "progress":    1 if today_actions & _SUBJECT_ACTIONS["math"] else 0,
            "total":       1,
            "completed":   bool(today_actions & _SUBJECT_ACTIONS["math"]),
            "locked":      False,
        },
        {
            "id":          "diary",
            "title":       "Write in Diary",
            "description": "Complete a diary entry today",
            "reward_lumi": 15,
            "progress":    1 if today_actions & _SUBJECT_ACTIONS["diary"] else 0,
            "total":       1,
            "completed":   bool(today_actions & _SUBJECT_ACTIONS["diary"]),
            "locked":      False,
        },
        {
            "id":          "all_four",
            "title":       "Island Master",
            "description": "Complete English + Math + Diary + Review today",
            "reward_lumi": 50,
            "progress":    sum(
                1 for s in _SUBJECT_ACTIONS if today_actions & _SUBJECT_ACTIONS[s]
            ),
            "total":       4,
            "completed":   all(today_actions & _SUBJECT_ACTIONS[s] for s in _SUBJECT_ACTIONS),
            "locked":      False,
        },
    ]

    xp_week = int(
        db.query(sqlfunc.sum(XPLog.xp_amount))
        .filter(XPLog.earned_date >= week_start.isoformat())
        .scalar() or 0
    )
    goals_rows = db.query(WeeklyGoal).filter(WeeklyGoal.is_active == 1).all()
    weekly_goals = [
        {
            "label":   g.label,
            "key":     g.key,
            "target":  g.target,
            "current": xp_week if g.key == "xp_earned" else 0,
        }
        for g in goals_rows
        if g.key == "xp_earned"
    ]

    return {
        "streak":            streak,
        "attendance_week":   attendance_week,
        "can_claim_today":   can_claim_today,
        "today_claimed":     today_claimed,
        "attendance_reward": ATTENDANCE_REWARD,
        "missions":          missions,
        "weekly_goals":      weekly_goals,
    }


# @tag ISLAND
@router.post("/daily/claim")
def daily_claim(db: Session = Depends(get_db)):
    """Claim today's attendance reward (30 Lumi). Deduped by daily_attendance source+date."""
    today = _today()

    studied = db.query(XPLog).filter(
        XPLog.earned_date == today.isoformat()
    ).first() is not None
    if not studied:
        raise HTTPException(400, "No study activity recorded today.")

    already = db.query(IslandLumiLog).filter(
        IslandLumiLog.source == "daily_attendance",
        IslandLumiLog.earned_date == today,
    ).first()
    if already:
        raise HTTPException(400, "Attendance reward already claimed today.")

    REWARD = 30
    result = le.earn_lumi(db, source="daily_attendance", amount=REWARD,
                          earned_date=today)
    db.commit()
    return {"ok": True, "lumi_earned": REWARD, "currency": result}


# ── Dev Tools (dev_mode only) ─────────────────────────────────────────────────

def _require_dev_mode(db: Session) -> None:
    """Block dev endpoints unless app_config dev_mode = 'true' (whitelist)."""
    cfg = db.query(AppConfig).filter_by(key="dev_mode").first()
    if not cfg or cfg.value != "true":
        raise HTTPException(status_code=403, detail="Dev mode is disabled.")


# @tag ISLAND
@router.post("/dev/seed")
def dev_seed(db: Session = Depends(get_db)):
    """Add 9999 Lumi + 5 of each evolution stone + max gauges on active chars."""
    _require_dev_mode(db)
    le.earn_lumi(db, source="dev_seed", amount=9999, earned_date=_today())
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
