"""
models/island.py — Island system ORM models (10 tables).
Section: Island
Dependencies: ._base.Base
API endpoints: /api/island/*
"""

from sqlalchemy import (
    Boolean, CheckConstraint, Column, Date, DateTime, Float,
    ForeignKey, Integer, String,
)
from sqlalchemy.sql import func

from ._base import Base


class IslandCharacter(Base):
    """Character catalog — 25 entries (5 per zone × 5 zones)."""
    __tablename__ = "island_characters"

    id                              = Column(Integer, primary_key=True)
    name                            = Column(String, nullable=False)
    zone                            = Column(String, nullable=False)           # forest/ocean/savanna/space/legend
    subject                         = Column(String, nullable=False)           # english/math/diary/review/all
    order_index                     = Column(Integer, nullable=False, default=1)
    description                     = Column(String, nullable=False, default="")
    images                          = Column(String, nullable=False, default="{}")  # JSON
    lumi_production                 = Column(Integer, nullable=False, default=5)
    xp_boost_pct                    = Column(Float,   nullable=False, default=1.5)
    xp_boost_a_pct                  = Column(Float,   nullable=False, default=3.0)  # A-form XP bonus %
    xp_boost_b_pct                  = Column(Float,   nullable=False, default=3.0)  # B-form extra lumi/day
    is_legend                       = Column(Boolean, nullable=False, default=False)
    unlock_requires_character_id    = Column(Integer, ForeignKey("island_characters.id"), nullable=True)
    is_available                    = Column(Boolean, nullable=False, default=False)
    evo_first_xp                    = Column(Integer, nullable=False, default=750)   # cumulative XP for 1st evo
    evo_second_xp                   = Column(Integer, nullable=False, default=1900)  # cumulative XP for 2nd evo


class IslandCharacterProgress(Base):
    """Gia's individual character progress. No UNIQUE on character_id — can adopt same char twice for A/B."""
    __tablename__ = "island_character_progress"

    id                          = Column(Integer, primary_key=True)
    character_id                = Column(Integer, ForeignKey("island_characters.id"), nullable=False)
    nickname                    = Column(String, nullable=False, default="")
    stage                       = Column(String, nullable=False, default="baby")  # baby/mid_a/mid_b/final_a/final_b
    level                       = Column(Integer, nullable=False, default=1)
    current_xp                  = Column(Integer, nullable=False, default=0)
    hunger                      = Column(Integer, nullable=False, default=80)
    happiness                   = Column(Integer, nullable=False, default=80)
    is_completed                = Column(Boolean, nullable=False, default=False)
    is_active                   = Column(Boolean, nullable=False, default=True)
    is_legend_type              = Column(Boolean, nullable=False, default=False)
    boost_active                = Column(Boolean, nullable=False, default=False)
    boost_subject               = Column(String, nullable=False, default="")
    last_production_date        = Column(String, nullable=True)
    last_decay_date             = Column(String, nullable=True)
    pos_x                       = Column(Integer, nullable=False, default=0)
    pos_y                       = Column(Integer, nullable=False, default=0)
    adopted_at                  = Column(DateTime, nullable=False, server_default=func.now())
    completed_at                = Column(DateTime, nullable=True)


class IslandCareLog(Base):
    """Care history — auto-deleted after 30 days by daily batch."""
    __tablename__ = "island_care_log"

    id                      = Column(Integer, primary_key=True)
    character_progress_id   = Column(Integer, ForeignKey("island_character_progress.id"), nullable=False)
    action                  = Column(String, nullable=False)               # feed/play/decay
    hunger_change           = Column(Integer, nullable=False, default=0)
    happiness_change        = Column(Integer, nullable=False, default=0)
    source                  = Column(String, nullable=False, default="")  # english/math/diary/review/food_item/auto_decay
    logged_at               = Column(DateTime, nullable=False, server_default=func.now())


class IslandShopItem(Base):
    """Shop catalog — 55 items seeded by migration 018."""
    __tablename__ = "island_shop_items"

    id                  = Column(Integer, primary_key=True)
    name                = Column(String, nullable=False)
    category            = Column(String, nullable=False)       # evolution/decoration/food
    sub_category        = Column(String, nullable=True)        # prop/building/nature/landscape/special/common/…
    zone                = Column(String, nullable=False, default="all")
    evolution_type      = Column(String, nullable=True)        # first_a/first_b/second/legend_first_a/legend_first_b/legend_second
    price               = Column(Integer, nullable=False, default=0)
    is_legend_currency  = Column(Boolean, nullable=False, default=False)
    image               = Column(String, nullable=False, default="")
    is_active           = Column(Boolean, nullable=False, default=True)
    description         = Column(String, nullable=False, default="")


class IslandInventory(Base):
    """Owned items (evolution stones, food, decorations)."""
    __tablename__ = "island_inventory"

    id                              = Column(Integer, primary_key=True)
    shop_item_id                    = Column(Integer, ForeignKey("island_shop_items.id"), nullable=False)
    item_type                       = Column(String, nullable=False)       # evolution/decoration/food
    quantity                        = Column(Integer, nullable=False, default=1)
    used_on_character_progress_id   = Column(Integer, ForeignKey("island_character_progress.id"), nullable=True)
    purchased_at                    = Column(DateTime, nullable=False, server_default=func.now())


class IslandPlacedItem(Base):
    """Decorations currently placed in a zone. shop_item_id is UNIQUE — one instance per item."""
    __tablename__ = "island_placed_items"

    id              = Column(Integer, primary_key=True)
    shop_item_id    = Column(Integer, ForeignKey("island_shop_items.id"), nullable=False, unique=True)
    zone            = Column(String, nullable=False)
    pos_x           = Column(Integer, nullable=False, default=0)
    pos_y           = Column(Integer, nullable=False, default=0)
    is_placed       = Column(Boolean, nullable=False, default=True)  # False = recalled to inventory
    placed_at       = Column(DateTime, nullable=False, server_default=func.now())


class IslandCurrency(Base):
    """Lumi balance — always a single row with id=1. Use upsert pattern."""
    __tablename__ = "island_currency"
    __table_args__ = (
        CheckConstraint("lumi >= 0",        name="ck_island_currency_lumi_nonneg"),
        CheckConstraint("legend_lumi >= 0", name="ck_island_currency_legend_nonneg"),
    )

    id              = Column(Integer, primary_key=True)
    lumi            = Column(Integer, nullable=False, default=0)
    legend_lumi     = Column(Integer, nullable=False, default=0)
    total_earned    = Column(Integer, nullable=False, default=0)
    updated_at      = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class IslandLumiLog(Base):
    """Lumi transaction history — auto-deleted after 90 days by daily batch."""
    __tablename__ = "island_lumi_log"

    id                      = Column(Integer, primary_key=True)
    currency_type           = Column(String, nullable=False, default="lumi")    # lumi/legend_lumi
    action                  = Column(String, nullable=False)                    # earn/spend/exchange
    amount                  = Column(Integer, nullable=False)
    source                  = Column(String, nullable=False, default="")        # english/math/diary/review/shop/exchange/production
    balance_after           = Column(Integer, nullable=False, default=0)
    legend_balance_after    = Column(Integer, nullable=False, default=0)
    character_progress_id   = Column(Integer, ForeignKey("island_character_progress.id"), nullable=True)
    earned_date             = Column(Date, nullable=True)                       # dedup guard for production logs
    created_at              = Column(DateTime, nullable=False, server_default=func.now())


class IslandLegendProgress(Base):
    """Legend character consecutive-day streak tracking."""
    __tablename__ = "island_legend_progress"

    id                  = Column(Integer, primary_key=True)
    character_id        = Column(Integer, ForeignKey("island_characters.id"), nullable=False)
    consecutive_days    = Column(Integer, nullable=False, default=0)
    total_days          = Column(Integer, nullable=False, default=0)
    last_completed_date = Column(Date, nullable=True)
    is_unlocked         = Column(Boolean, nullable=False, default=False)
    is_completed        = Column(Boolean, nullable=False, default=False)
    completed_at        = Column(DateTime, nullable=True)


class IslandZoneStatus(Base):
    """Zone unlock state — 5 rows seeded by migration 018."""
    __tablename__ = "island_zone_status"

    id                  = Column(Integer, primary_key=True)
    zone                = Column(String, nullable=False, unique=True)
    is_unlocked         = Column(Boolean, nullable=False, default=False)
    unlocked_at         = Column(DateTime, nullable=True)
    first_completed_at  = Column(DateTime, nullable=True)


__all__ = [
    "IslandCharacter",
    "IslandCharacterProgress",
    "IslandCareLog",
    "IslandShopItem",
    "IslandInventory",
    "IslandPlacedItem",
    "IslandCurrency",
    "IslandLumiLog",
    "IslandLegendProgress",
    "IslandZoneStatus",
]
