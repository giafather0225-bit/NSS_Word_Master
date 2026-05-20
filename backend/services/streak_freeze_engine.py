"""
services/streak_freeze_engine.py — Lumi-consumable Streak Freeze

A Streak Freeze is a one-shot item the child buys in the Reward Shop
(category 'streak_freeze', seeded by migration 063). Consuming one marks
the chosen date as "frozen": streak_engine._evaluate_streak treats it
exactly like an approved Day-Off and keeps the streak alive.

Storage:
  streak_freezes(used_date UNIQUE) — one freeze per calendar day
  island_inventory                 — quantity decremented on consume
"""

from datetime import date
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.models import IslandInventory, IslandShopItem
from backend.services import streak_engine


_CATEGORY = "streak_freeze"


def _today() -> str:
    return date.today().isoformat()


def available_count(db: Session) -> int:
    """Total number of Streak Freezes the child currently owns."""
    rows = (
        db.query(IslandInventory)
        .join(IslandShopItem, IslandInventory.shop_item_id == IslandShopItem.id)
        .filter(IslandShopItem.category == _CATEGORY)
        .all()
    )
    return sum(r.quantity for r in rows)


def is_day_frozen(db: Session, day: Optional[str] = None) -> bool:
    """True if the given (or today's) date has a streak_freeze recorded."""
    target = day or _today()
    row = db.execute(
        text("SELECT 1 FROM streak_freezes WHERE used_date = :d LIMIT 1"),
        {"d": target},
    ).first()
    return bool(row)


def status(db: Session) -> dict:
    """Combined view for the UI: today's freeze state + inventory count."""
    return {
        "today":           _today(),
        "today_frozen":    is_day_frozen(db),
        "available_count": available_count(db),
    }


class FreezeError(Exception):
    """Raised when a freeze can't be applied (already frozen / no inventory)."""


def apply_freeze(db: Session, day: Optional[str] = None) -> dict:
    """Consume one Streak Freeze and mark `day` (default today) as frozen.

    Atomicity: the inventory decrement, freeze-row insert, and streak
    re-evaluation share one commit. On any failure we rollback and raise
    FreezeError — leaving inventory and streak_freezes in sync.

    Returns the updated status dict.
    """
    target = day or _today()

    if is_day_frozen(db, target):
        raise FreezeError("This day is already frozen.")

    # Find the cheapest non-empty inventory row in the streak_freeze
    # category. Sorted by quantity ASC just to drain low-quantity rows first.
    inv_row = (
        db.query(IslandInventory)
        .join(IslandShopItem, IslandInventory.shop_item_id == IslandShopItem.id)
        .filter(
            IslandShopItem.category == _CATEGORY,
            IslandInventory.quantity > 0,
        )
        .order_by(IslandInventory.quantity.asc())
        .first()
    )
    if inv_row is None:
        raise FreezeError("You have no Streak Shields. Buy one in the shop first.")

    inv_row.quantity -= 1
    db.execute(
        text(
            "INSERT INTO streak_freezes (used_date, inventory_id) "
            "VALUES (:d, :iid)"
        ),
        {"d": target, "iid": inv_row.id},
    )
    db.commit()

    # Re-evaluate streak for the frozen date so the side-effects (streak
    # count, lumi award if maintained today) land immediately.
    log = streak_engine.get_or_create_streak_log(db, day=target)
    streak_engine._evaluate_streak(db, log, commit=True)

    return status(db)
