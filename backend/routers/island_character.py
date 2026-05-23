"""
routers/island_character.py — Character catalog, adoption, evolution, and care.
Section: Island
Dependencies: _island_common, services.island_service, services.island_care_engine
API endpoints: /api/island/characters, /character/*, /evolve/*, /care/*
"""

import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.island import (
    IslandCharacter, IslandCharacterProgress, IslandCareLog,
    IslandShopItem, IslandInventory, IslandLegendProgress, IslandZoneStatus,
)
from backend.services import island_care_engine as care
from backend.services import island_service as svc
from backend.services.island_service import EvolutionError
from backend.routers._island_common import (
    AdoptBody, EvolveBranchBody, FeedBody,
    FOOD_XP, ZONE_UNLOCK_CHAIN,
    cfg, island_today_start, prog_dict,
)

router = APIRouter(prefix="/api/island", tags=["island"])


# @tag ISLAND
@router.get("/characters")
def character_catalog(zone: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(IslandCharacter)
    if zone:
        q = q.filter(IslandCharacter.zone == zone)
    chars = q.order_by(IslandCharacter.zone, IslandCharacter.order_index).all()

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
            "images": char.images or "{}",
            "progress": [prog_dict(p, char_map[p.character_id]) for p in progs],
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

    legend_char_ids = {p.character_id for p, _ in rows if p.is_legend_type}
    legend_days_by_char: dict[int, int] = {}
    if legend_char_ids:
        legend_rows = (
            db.query(IslandLegendProgress)
            .filter(IslandLegendProgress.character_id.in_(legend_char_ids))
            .all()
        )
        legend_days_by_char = {lr.character_id: lr.consecutive_days for lr in legend_rows}
    legend_days = {p.id: legend_days_by_char.get(p.character_id, 0) for p, _ in rows if p.is_legend_type}

    return {
        "characters": [
            prog_dict(p, c, consecutive_days=legend_days.get(p.id, 0))
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
    return {"characters": [prog_dict(p, c) for p, c in rows]}


# @tag ISLAND
@router.get("/character/silhouette")
def character_silhouette(db: Session = Depends(get_db)):
    """Return all characters with adoptable/silhouette/locked status."""
    test_mode = cfg(db, "test_mode") == "true"

    chars = db.query(IslandCharacter).order_by(
        IslandCharacter.zone, IslandCharacter.order_index).all()

    zone_unlocked_map: dict[str, bool] = {
        row.zone: bool(row.is_unlocked)
        for row in db.query(IslandZoneStatus).all()
    }
    completed_char_ids: set[int] = {
        row.character_id
        for row in db.query(IslandCharacterProgress.character_id)
        .filter(IslandCharacterProgress.is_completed == True)
        .all()
    }
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
        # In test mode, all zones/prereqs are considered unlocked.
        effective_zone_unlocked = True if test_mode else zone_unlocked
        effective_prereq = True if test_mode else has_prereq
        effective_available = True if test_mode else char.is_available
        result.append({
            "character_id": char.id, "name": char.name, "zone": char.zone,
            "order_index": char.order_index, "is_available": char.is_available,
            "zone_unlocked": effective_zone_unlocked, "prereq_met": effective_prereq,
            "adoptable": effective_available and effective_zone_unlocked and effective_prereq and not_active,
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
    test_mode = cfg(db, "test_mode") == "true"
    if not char.is_available and not test_mode:
        raise HTTPException(400, "This character is not yet available.")
    already_active = db.query(IslandCharacterProgress).filter(
        IslandCharacterProgress.character_id == char.id,
        IslandCharacterProgress.is_completed == False,
    ).first()
    if already_active:
        raise HTTPException(400, "This character is already being raised.")
    if char.unlock_requires_character_id and not test_mode:
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
    return prog_dict(prog, char)


# @tag ISLAND
@router.post("/character/evolve")
def character_evolve(body: EvolveBranchBody, db: Session = Depends(get_db)):
    """Evolve a character by choosing branch 'a' or 'b'."""
    prog = db.get(IslandCharacterProgress, body.character_progress_id)
    if prog is None:
        raise HTTPException(404, "Character progress not found.")

    # ── P1-12 router-level guards (defense-in-depth before calling the service) ──
    _FINAL = {"final_a", "final_b"}
    if prog.is_completed or (prog.stage in _FINAL):
        raise HTTPException(400, "This character has already reached their final form.")
    if not prog.is_legend_type and ((prog.hunger or 0) < 20 or (prog.happiness or 0) < 20):
        low = []
        if (prog.hunger or 0) < 20:
            low.append(f"Hunger ({prog.hunger})")
        if (prog.happiness or 0) < 20:
            low.append(f"Happiness ({prog.happiness})")
        raise HTTPException(
            400,
            f"Both gauges must be at least 20 to evolve. Low: {', '.join(low)}.",
        )

    stage = prog.stage or "baby"
    branch = (body.branch or "a").lower()
    if branch not in ("a", "b"):
        raise HTTPException(status_code=400, detail="branch must be 'a' or 'b'.")
    if prog.is_legend_type:
        stone = "legend_first_a" if stage == "baby" and branch == "a" else \
                "legend_first_b" if stage == "baby" and branch == "b" else \
                "legend_second"
    else:
        stone = "first_a" if stage == "baby" and branch == "a" else \
                "first_b" if stage == "baby" and branch == "b" else \
                "second"
    test_mode = cfg(db, "test_mode") == "true"
    try:
        result = svc.execute_evolution(db, body.character_progress_id, stone, test_mode=test_mode)

        # ── Legend zone unlock: all 4 main zones need ≥1 first-evolution char ──
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
                    for z in ZONE_UNLOCK_CHAIN
                )
                if all_first_evo:
                    legend_row.is_unlocked = True
                    legend_row.unlocked_at = datetime.now(timezone.utc)
                    result["zone_unlocked"] = "legend"
                    logger.info("Legend zone unlocked — all 4 main zones have first-evolution characters")

        # ── Sequential zone unlock: completing zone[i] → unlock zone[i+1] ──
        if result.get("is_completed") and not prog.is_legend_type:
            char = db.get(IslandCharacter, prog.character_id)
            if char and char.zone in ZONE_UNLOCK_CHAIN:
                idx = ZONE_UNLOCK_CHAIN.index(char.zone)
                if idx + 1 < len(ZONE_UNLOCK_CHAIN):
                    next_zone = ZONE_UNLOCK_CHAIN[idx + 1]
                    next_row = db.query(IslandZoneStatus).filter_by(zone=next_zone).first()
                    if next_row and not next_row.is_unlocked:
                        next_row.is_unlocked = True
                        next_row.unlocked_at = datetime.now(timezone.utc)
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
    """Return both evolution branches so the UI can present a choice."""
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

    subject_label = (char.subject or "study").capitalize() if char else "Study"
    xp_base  = round(char.xp_boost_pct, 1)    if char else 1.5
    xp_a_add = round(char.xp_boost_a_pct, 1)  if char else 3.0
    lumi_b   = round(char.xp_boost_b_pct, 1)  if char else 3.0
    lumi_prod = int(char.lumi_production)      if char else 5
    images = char.images if char else "{}"

    if is_mid:
        branch_a_ability  = "XP Champion"
        branch_a_desc     = f"+{xp_base + xp_a_add}% {subject_label} XP boost — active immediately after evolution."
        branch_a_boost    = f"+{xp_base + xp_a_add}% {subject_label} XP"
        branch_b_ability  = "Lumi Producer"
        branch_b_desc     = f"Produces {lumi_prod + lumi_b:.0f} Lumi/day — stacks with other completed characters."
        branch_b_boost    = f"{lumi_prod + lumi_b:.0f} Lumi / day"
    else:
        branch_a_ability  = "XP Path"
        branch_a_desc     = f"Grows into the XP branch. Final form gives +{xp_base + xp_a_add}% {subject_label} XP."
        branch_a_boost    = f"+{xp_base + xp_a_add}% XP (final form)"
        branch_b_ability  = "Lumi Path"
        branch_b_desc     = f"Grows into the Lumi branch. Final form produces {lumi_prod + lumi_b:.0f} Lumi/day."
        branch_b_boost    = f"{lumi_prod + lumi_b:.0f} Lumi/day (final form)"

    return {
        "valid": True, "stage": stage, "images": images,
        "branch_a": {
            "stone": stone_a, "target_stage": target_a, "ability": branch_a_ability,
            "description": branch_a_desc, "boost_preview": branch_a_boost, "boost_icon": "zap",
        },
        "branch_b": {
            "stone": stone_b, "target_stage": target_b, "ability": branch_b_ability,
            "description": branch_b_desc, "boost_preview": branch_b_boost, "boost_icon": "gem",
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
# Care System
# ─────────────────────────────────────────────────────────────────────────────

# @tag ISLAND
@router.get("/care/{character_progress_id}")
def care_status(character_progress_id: int, db: Session = Depends(get_db)):
    prog = db.get(IslandCharacterProgress, character_progress_id)
    if prog is None:
        raise HTTPException(404, "Character progress not found.")
    char = db.get(IslandCharacter, prog.character_id)

    stage = prog.stage or "baby"
    is_mid = stage in ("mid_a", "mid_b")
    is_final = stage in ("final_a", "final_b")
    xp_to_next = (char.evo_second_xp if is_mid else char.evo_first_xp) if char else 100
    current_xp = prog.current_xp or 0

    if is_final or prog.is_completed:
        stone_needed = "None"
        can_evolve = False
    elif prog.is_legend_type:
        stone_needed = "legend_first_a" if stage == "baby" else "legend_second"
        min_level = 10 if is_mid else 5
        can_evolve = (current_xp >= xp_to_next and (prog.level or 1) >= min_level
                      and prog.hunger >= 20 and prog.happiness >= 20)
    else:
        stone_needed = "first_a" if stage == "baby" else "second"
        min_level = 10 if is_mid else 5
        can_evolve = (current_xp >= xp_to_next and (prog.level or 1) >= min_level
                      and prog.hunger >= 20 and prog.happiness >= 20)

    legend_prog = None
    if prog.is_legend_type:
        from backend.models.island import IslandLegendProgress
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
            "zone": char.zone if char else "",
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
        IslandCareLog.source.like(f"food_{shop_item.id}_%"),
        IslandCareLog.logged_at >= island_today_start(),
    ).first()
    if used_today:
        raise HTTPException(400, f"{shop_item.name} already used on this character today.")

    xp_gain = FOOD_XP.get(shop_item.name)
    if xp_gain is None:
        logger.warning("Unknown food item name %r (id=%s) — defaulting to 50 XP. "
                       "Update FOOD_XP if the shop catalog changed.", shop_item.name, shop_item.id)
        xp_gain = 50
    prog = db.get(IslandCharacterProgress, body.character_progress_id)
    if prog is None:
        raise HTTPException(404, "Character progress not found.")

    level_before = care._calc_level(prog.current_xp or 0)
    prog.current_xp = (prog.current_xp or 0) + xp_gain
    level_after  = care._calc_level(prog.current_xp)
    if level_after != prog.level:
        prog.level = level_after

    inv.quantity -= 1
    inv.used_on_character_progress_id = body.character_progress_id
    if inv.quantity <= 0:
        db.delete(inv)

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
