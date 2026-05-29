"""
routers/_island_common.py — Shared constants, helpers, and Pydantic schemas for island routers.
Section: Island
Dependencies: models.island, models.system, services.lumi_engine
API endpoints: none
"""

import logging
from datetime import date, datetime, timedelta, timezone
from typing import Optional

logger = logging.getLogger(__name__)

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.models.island import IslandCharacter, IslandCharacterProgress
from backend.models.system import AppConfig
from backend.services import lumi_engine as le

# ── Config key whitelist for public reads ─────────────────────────────────────
ISLAND_CONFIG_KEYS = {
    "island_initialized", "island_on", "lumi_exchange_rate",
    "lumi_rule_english_stage", "lumi_rule_english_final",
    "lumi_rule_math_lesson", "lumi_rule_math_unit",
    "lumi_rule_diary", "lumi_rule_review", "lumi_rule_streak",
    "lumi_boost_total", "lumi_boost_english", "lumi_boost_math",
    "lumi_boost_diary", "lumi_boost_review",
}

FOOD_XP = {"Small Food": 50, "Big Food": 150, "Special Food": 300}

# Zone sequential unlock chain (ISLAND_SPEC §Zone).
ZONE_UNLOCK_CHAIN = ["forest", "ocean", "savanna", "space"]

# Subject detection from XPLog action for legend daily check.
SUBJECT_ACTIONS: dict[str, set[str]] = {
    "english": {"word_correct", "stage_complete", "final_test_pass", "unit_test_pass",
                "daily_words_complete", "weekly_test_pass", "mywords_weekly_test_pass"},
    "math":    {"math_lesson_complete", "math_unit_test_pass", "math_kangaroo_complete",
                "math_kangaroo_80", "math_kangaroo_perfect"},
    "diary":   {"journal_complete"},
    "review":  {"review_complete"},
}


def island_today() -> date:
    # Use local date (date.today()) — not UTC — so island date tracking stays
    # consistent with XPLog.earned_date which is written by award_xp() using
    # date.today(). Using UTC caused off-by-one date errors in Korea (UTC+9)
    # between midnight and 09:00 KST: island showed yesterday as "today" and
    # attendance checks always returned False for morning study sessions.
    return date.today()


def island_today_start() -> datetime:
    # Midnight local time (naive) — used for log timestamp range queries.
    return datetime.combine(date.today(), datetime.min.time())


def cfg(db: Session, key: str, default: str = "") -> str:
    row = db.query(AppConfig).filter_by(key=key).first()
    return row.value if row else default


def set_cfg(db: Session, key: str, value: str) -> None:
    row = db.query(AppConfig).filter_by(key=key).first()
    if row:
        row.value = value
    else:
        db.add(AppConfig(key=key, value=value))


def prog_dict(
    prog: IslandCharacterProgress,
    char: IslandCharacter,
    consecutive_days: int = 0,
) -> dict:
    stage = prog.stage or "baby"
    is_mid   = stage in ("mid_a", "mid_b")
    xp_needed = (char.evo_second_xp if is_mid else char.evo_first_xp) if char else 100
    min_level = 10 if is_mid else 5
    ready_to_evolve = (
        not prog.is_completed
        and stage not in ("final_a", "final_b")
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
    branch: str = Field("", max_length=2)

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
