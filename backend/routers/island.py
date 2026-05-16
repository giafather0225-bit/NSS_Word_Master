"""
routers/island.py — Island infrastructure: status, onboarding, zone, daily batch,
                    boost, notifications, config, stats, daily screen/claim (14 endpoints).
Section: Island
Dependencies: services.lumi_engine, island_care_engine, island_production_engine, island_service
API endpoints: /api/island/*
"""

import logging
from datetime import date, datetime, timedelta, timezone
from typing import Optional

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func as sqlfunc
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.island import (
    IslandCharacter, IslandCharacterProgress,
    IslandLumiLog, IslandZoneStatus,
)
from backend.models.gamification import XPLog
from backend.models.goals import WeeklyGoal
from backend.services import lumi_engine as le
from backend.services import island_care_engine as care
from backend.services import island_production_engine as prod
from backend.routers._island_common import (
    ISLAND_CONFIG_KEYS, SUBJECT_ACTIONS, ZONE_UNLOCK_CHAIN,
    ZoneUnlockBody, ConfigUpdateBody,
    cfg, set_cfg, prog_dict,
    island_today, island_today_start,
)

router = APIRouter(prefix="/api/island", tags=["island"])


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
        "island_on": cfg(db, "island_on", "true") == "true",
        "initialized": cfg(db, "island_initialized") == "true",
        "currency": le.get_balance(db),
        "zones": [{"zone": z.zone, "is_unlocked": z.is_unlocked} for z in zones],
        "active_characters": [prog_dict(p, c) for p, c in active],
        "completed_characters": [prog_dict(p, c) for p, c in completed],
        "completed_count": len(completed),
    }


# @tag ISLAND
@router.get("/onboarding/status")
def onboarding_status(db: Session = Depends(get_db)):
    return {"initialized": cfg(db, "island_initialized") == "true"}


# @tag ISLAND
@router.post("/onboarding/complete")
def onboarding_complete(db: Session = Depends(get_db)):
    """Mark island as initialized and unlock all 4 main zones.

    Zone 1-4 sequential opening is a UX-only onboarding effect; all main zones
    must be playable immediately after onboarding completes.
    """
    set_cfg(db, "island_initialized", "true")
    now = datetime.now(timezone.utc)
    for zone in ZONE_UNLOCK_CHAIN:
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
# 12.9 Boost & Notifications
# ─────────────────────────────────────────────────────────────────────────────

# @tag ISLAND @tag XP
@router.get("/boost/status")
def boost_status(db: Session = Depends(get_db)):
    keys = ["lumi_boost_total", "lumi_boost_english", "lumi_boost_math",
            "lumi_boost_diary", "lumi_boost_review"]
    return {k: float(cfg(db, k, "0")) for k in keys}


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
        if active_char is None and not prog.is_legend_type:
            active_char = {
                "name":      prog.nickname or char.name,
                "hunger":    prog.hunger,
                "happiness": prog.happiness,
            }

        if (not prog.is_legend_type) and (prog.hunger < 40 or prog.happiness < 40):
            hungry.append({
                "nickname":  prog.nickname or char.name,
                "name":      char.name,
                "hunger":    prog.hunger,
                "happiness": prog.happiness,
            })

        if not prog.is_legend_type:
            stage = prog.stage or "baby"
            is_final = stage in ("final_a", "final_b")
            xp_needed = (char.evo_second_xp if stage in ("mid_a", "mid_b") else char.evo_first_xp) if char else 100
            if not is_final and not prog.is_completed:
                if (prog.current_xp or 0) >= xp_needed and prog.hunger >= 20 and prog.happiness >= 20:
                    evolvable.append({"nickname": prog.nickname or char.name, "name": char.name})

    _PASSIVE_PREFIXES = ("production", "dev_", "exchange", "daily_attendance")
    today_logs = (
        db.query(IslandLumiLog)
        .filter(IslandLumiLog.earned_date == island_today())
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
    from backend.models.system import AppConfig
    rows = db.query(AppConfig).filter(AppConfig.key.in_(ISLAND_CONFIG_KEYS)).all()
    return {"config": {r.key: r.value for r in rows}}


# @tag ISLAND
@router.post("/config/update")
def config_update(body: ConfigUpdateBody, db: Session = Depends(get_db)):
    if body.key not in ISLAND_CONFIG_KEYS:
        raise HTTPException(400, f"Config key '{body.key}' is not editable here.")
    set_cfg(db, body.key, body.value)
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
        "boost": {k: float(cfg(db, k, "0")) for k in [
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

    today      = island_today()
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
            "progress":    1 if today_actions & SUBJECT_ACTIONS["english"] else 0,
            "total":       1,
            "completed":   bool(today_actions & SUBJECT_ACTIONS["english"]),
            "locked":      False,
        },
        {
            "id":          "math",
            "title":       "Study Math",
            "description": "Complete any Math activity today",
            "reward_lumi": 20,
            "progress":    1 if today_actions & SUBJECT_ACTIONS["math"] else 0,
            "total":       1,
            "completed":   bool(today_actions & SUBJECT_ACTIONS["math"]),
            "locked":      False,
        },
        {
            "id":          "diary",
            "title":       "Write in Diary",
            "description": "Complete a diary entry today",
            "reward_lumi": 15,
            "progress":    1 if today_actions & SUBJECT_ACTIONS["diary"] else 0,
            "total":       1,
            "completed":   bool(today_actions & SUBJECT_ACTIONS["diary"]),
            "locked":      False,
        },
        {
            "id":          "all_four",
            "title":       "Island Master",
            "description": "Complete English + Math + Diary + Review today",
            "reward_lumi": 50,
            "progress":    sum(
                1 for s in SUBJECT_ACTIONS if today_actions & SUBJECT_ACTIONS[s]
            ),
            "total":       4,
            "completed":   all(today_actions & SUBJECT_ACTIONS[s] for s in SUBJECT_ACTIONS),
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
    today = island_today()

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
