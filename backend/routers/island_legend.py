"""
routers/island_legend.py — Island legend system (3 endpoints).
Section: Island
Dependencies: models.island, models.gamification, services.island_care_engine
API endpoints: /api/island/legend/*
"""

import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.island import (
    IslandCharacter, IslandCharacterProgress, IslandLegendProgress, IslandZoneStatus,
)
from backend.models.gamification import XPLog
from backend.services import island_care_engine as care
from backend.routers._island_common import (
    SUBJECT_ACTIONS,
    island_today, island_today_start,
)

router = APIRouter(prefix="/api/island", tags=["island"])


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
    today = island_today()
    today_start = island_today_start()
    today_actions = {
        row[0] for row in
        db.query(XPLog.action).filter(XPLog.created_at >= today_start).distinct().all()
    }
    subjects_done = {
        subj: bool(today_actions & actions)
        for subj, actions in SUBJECT_ACTIONS.items()
    }
    all_four = all(subjects_done.values())

    if not all_four:
        return {"all_four_done": False, "subjects": subjects_done}

    legend_progs = (
        db.query(IslandCharacterProgress)
        .filter(IslandCharacterProgress.is_legend_type == True,
                IslandCharacterProgress.is_active == True)
        .all()
    )

    updated = []
    for prog in legend_progs:
        care.apply_study_gain(db, prog.id, "legend_4subject")

        lp = db.query(IslandLegendProgress).filter_by(character_id=prog.character_id).first()
        if lp is None:
            lp = IslandLegendProgress(character_id=prog.character_id)
            db.add(lp)
            db.flush()

        if lp.last_completed_date == today:
            continue

        if lp.last_completed_date and (today - lp.last_completed_date).days > 1:
            if lp.consecutive_days > 0:
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

    # NOTE: Do NOT auto-unlock here — this is a read-only GET endpoint.
    # Legend zone unlocking is handled by /character/evolve.
    legend_zone = db.query(IslandZoneStatus).filter_by(zone="legend").first()
    legend_in_db = bool(legend_zone and legend_zone.is_unlocked)

    return {"zones": zone_status, "legend_unlocked": legend_in_db}
