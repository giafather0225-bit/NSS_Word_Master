"""
services/lumi_engine.py — Lumi currency earn/spend/exchange logic.
Section: Island
Dependencies: models.island, models.system (AppConfig)
API endpoints: called by routers/island.py and study/math/diary/review routers
"""

from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.models.island import IslandCurrency, IslandLumiLog
from backend.models.system import AppConfig

# Default exchange rate — overridden by app_config key `lumi_exchange_rate`.
_DEFAULT_EXCHANGE_RATE = 100


class InsufficientLumiError(Exception):
    """Raised when a spend or exchange would push the balance below zero."""


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _get_currency(db: Session) -> IslandCurrency:
    """Fetch or create the single currency row (id=1)."""
    row = db.get(IslandCurrency, 1)
    if row is None:
        row = IslandCurrency(id=1, lumi=0, legend_lumi=0, total_earned=0)
        db.add(row)
        db.flush()
    return row


def _get_exchange_rate(db: Session) -> int:
    cfg = db.query(AppConfig).filter_by(key="lumi_exchange_rate").first()
    if cfg:
        try:
            return max(1, int(cfg.value))
        except (TypeError, ValueError):
            pass
    return _DEFAULT_EXCHANGE_RATE


def _log(
    db: Session,
    *,
    currency_type: str,
    action: str,
    amount: int,
    source: str,
    balance_after: int,
    legend_balance_after: int,
    character_progress_id: Optional[int] = None,
    earned_date: Optional[date] = None,
) -> None:
    db.add(IslandLumiLog(
        currency_type=currency_type,
        action=action,
        amount=amount,
        source=source,
        balance_after=balance_after,
        legend_balance_after=legend_balance_after,
        character_progress_id=character_progress_id,
        earned_date=earned_date,
        created_at=datetime.now(timezone.utc),
    ))


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

# @tag ISLAND @tag XP @tag AWARD
def get_balance(db: Session) -> dict:
    """Return current lumi and legend_lumi balances."""
    row = _get_currency(db)
    return {
        "lumi": row.lumi,
        "legend_lumi": row.legend_lumi,
        "total_earned": row.total_earned,
    }


# @tag ISLAND @tag AWARD
def earn_lumi(
    db: Session,
    source: str,
    amount: int,
    character_progress_id: Optional[int] = None,
    earned_date: Optional[date] = None,
) -> dict:
    """
    Award lumi from a study activity.

    Args:
        source: e.g. "english", "math", "diary", "review", "streak", "production"
        amount: positive integer
        character_progress_id: set for daily production logs (dedup guard)
        earned_date: set for production logs to prevent double-award on same day

    Returns:
        {"lumi": <new_balance>, "legend_lumi": <balance>, "earned": <amount>}
    """
    if amount <= 0:
        raise ValueError(f"earn_lumi: amount must be positive, got {amount}")

    row = _get_currency(db)
    row.lumi += amount
    row.total_earned += amount
    row.updated_at = datetime.now(timezone.utc)

    _log(
        db,
        currency_type="lumi",
        action="earn",
        amount=amount,
        source=source,
        balance_after=row.lumi,
        legend_balance_after=row.legend_lumi,
        character_progress_id=character_progress_id,
        earned_date=earned_date,
    )
    db.flush()
    return {"lumi": row.lumi, "legend_lumi": row.legend_lumi, "earned": amount}


# @tag ISLAND @tag SHOP
def spend_lumi(db: Session, amount: int, source: str) -> dict:
    """
    Deduct lumi for a purchase.

    Raises:
        InsufficientLumiError: if balance < amount (service-level guard before DB CHECK)
        ValueError: if amount <= 0

    Returns:
        {"lumi": <new_balance>, "legend_lumi": <balance>, "spent": <amount>}
    """
    if amount <= 0:
        raise ValueError(f"spend_lumi: amount must be positive, got {amount}")

    row = _get_currency(db)
    if row.lumi < amount:
        raise InsufficientLumiError(
            f"Need {amount} Lumi but only {row.lumi} available."
        )

    row.lumi -= amount
    row.updated_at = datetime.now(timezone.utc)

    _log(
        db,
        currency_type="lumi",
        action="spend",
        amount=-amount,
        source=source,
        balance_after=row.lumi,
        legend_balance_after=row.legend_lumi,
    )
    db.flush()
    return {"lumi": row.lumi, "legend_lumi": row.legend_lumi, "spent": amount}


# @tag ISLAND @tag AWARD
def earn_legend_lumi(db: Session, amount: int, source: str) -> dict:
    """
    Award legend lumi (from exchange or other sources).

    Returns:
        {"lumi": <balance>, "legend_lumi": <new_balance>, "earned": <amount>}
    """
    if amount <= 0:
        raise ValueError(f"earn_legend_lumi: amount must be positive, got {amount}")

    row = _get_currency(db)
    row.legend_lumi += amount
    row.updated_at = datetime.now(timezone.utc)

    _log(
        db,
        currency_type="legend_lumi",
        action="earn",
        amount=amount,
        source=source,
        balance_after=row.lumi,
        legend_balance_after=row.legend_lumi,
    )
    db.flush()
    return {"lumi": row.lumi, "legend_lumi": row.legend_lumi, "earned": amount}


# @tag ISLAND @tag SHOP
def spend_legend_lumi(db: Session, amount: int, source: str) -> dict:
    """
    Deduct legend lumi for a legend-zone purchase.

    Raises:
        InsufficientLumiError: if legend_lumi balance < amount
        ValueError: if amount <= 0

    Returns:
        {"lumi": <balance>, "legend_lumi": <new_balance>, "spent": <amount>}
    """
    if amount <= 0:
        raise ValueError(f"spend_legend_lumi: amount must be positive, got {amount}")

    row = _get_currency(db)
    if row.legend_lumi < amount:
        raise InsufficientLumiError(
            f"Need {amount} Legend Lumi but only {row.legend_lumi} available."
        )

    row.legend_lumi -= amount
    row.updated_at = datetime.now(timezone.utc)

    _log(
        db,
        currency_type="legend_lumi",
        action="spend",
        amount=-amount,
        source=source,
        balance_after=row.lumi,
        legend_balance_after=row.legend_lumi,
    )
    db.flush()
    return {"lumi": row.lumi, "legend_lumi": row.legend_lumi, "spent": amount}


# @tag ISLAND @tag SHOP
def exchange_lumi(db: Session, lumi_amount: int) -> dict:
    """
    Convert lumi → legend lumi at the configured rate (default 100:1).

    lumi_amount must be an exact multiple of the exchange rate.

    Raises:
        InsufficientLumiError: if lumi balance < lumi_amount
        ValueError: if lumi_amount is not a positive multiple of the rate

    Returns:
        {
            "lumi": <new_lumi_balance>,
            "legend_lumi": <new_legend_lumi_balance>,
            "lumi_spent": <lumi_amount>,
            "legend_lumi_earned": <legend_gained>,
            "rate": <exchange_rate>,
        }
    """
    if lumi_amount <= 0:
        raise ValueError(f"exchange_lumi: lumi_amount must be positive, got {lumi_amount}")

    rate = _get_exchange_rate(db)
    if lumi_amount % rate != 0:
        raise ValueError(
            f"exchange_lumi: lumi_amount ({lumi_amount}) must be a multiple of the rate ({rate})."
        )

    legend_gained = lumi_amount // rate

    row = _get_currency(db)
    if row.lumi < lumi_amount:
        raise InsufficientLumiError(
            f"Need {lumi_amount} Lumi to exchange but only {row.lumi} available."
        )

    row.lumi -= lumi_amount
    row.legend_lumi += legend_gained
    row.updated_at = datetime.now(timezone.utc)

    now = datetime.now(timezone.utc)

    # Log the spend side.
    db.add(IslandLumiLog(
        currency_type="lumi",
        action="exchange",
        amount=-lumi_amount,
        source="exchange",
        balance_after=row.lumi,
        legend_balance_after=row.legend_lumi,
        created_at=now,
    ))
    # Log the earn side.
    db.add(IslandLumiLog(
        currency_type="legend_lumi",
        action="exchange",
        amount=legend_gained,
        source="exchange",
        balance_after=row.lumi,
        legend_balance_after=row.legend_lumi,
        created_at=now,
    ))
    db.flush()

    return {
        "lumi": row.lumi,
        "legend_lumi": row.legend_lumi,
        "lumi_spent": lumi_amount,
        "legend_lumi_earned": legend_gained,
        "rate": rate,
    }
